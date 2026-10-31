#!/usr/bin/env node
// fake-memory-bank.js — stand-in for the memory-bank CLI `search` subcommand, used by
// test_search_tier0_mb.sh. Prints blocks in the same shape as memory-bank 1.6.0:
//
//   Found N relevant conversations:
//
//   1. [<project>, <date>] - 55% match          (vector blocks carry "% match")
//      "<first words>"
//      Lines A-B in <archive>.jsonl (12.3KB, 456 lines)
//
// Modes follow the real CLI: --vector = semantic only, --text = exact text only,
// neither = both (semantic top-N + text top-N, merged without a cut → up to 2N).
//
// Knobs (environment):
//   FAKE_MB_FAIL=1        exit 1 with a message on stderr, nothing on stdout
//   FAKE_MB_FAIL_MODE=x   exit 1 only when mode x (vector|text) is requested
//   FAKE_MB_EMPTY=1       print "No results found." (rc 0)
//   FAKE_MB_OVERLAP=1     the first text block points at the same Lines/jsonl as vector block 1
//                         (with a different size suffix, so the dedupe key must drop the "(…)" tail)
//   FAKE_MB_IGNORE_LIMIT=N  return N blocks per mode whatever --limit says (a CLI that ignores it)
//   FAKE_MB_LOG=<file>    append one line per call: "<mode> <limit>"
'use strict';
const fs = require('fs');

const argv = process.argv.slice(2);
if (argv[0] !== 'search') {
  process.stderr.write('fake: only `search` is supported\n');
  process.exit(2);
}
let mode = 'both';
let limit = 10;
for (let i = 1; i < argv.length; i++) {
  if (argv[i] === '--vector') mode = 'vector';
  else if (argv[i] === '--text') mode = 'text';
  else if (argv[i] === '--both') mode = 'both';
  else if (argv[i] === '--limit') limit = parseInt(argv[++i], 10);
}
if (process.env.FAKE_MB_IGNORE_LIMIT) limit = parseInt(process.env.FAKE_MB_IGNORE_LIMIT, 10);
if (process.env.FAKE_MB_LOG) fs.appendFileSync(process.env.FAKE_MB_LOG, `${mode} ${limit}\n`);

if (process.env.FAKE_MB_FAIL === '1' || process.env.FAKE_MB_FAIL_MODE === mode) {
  process.stderr.write('Error: database is locked\n');
  process.exit(1);
}
// Real CLI prints model-load chatter before results; the Tier 0 block must not count it.
process.stdout.write('Loading embedding model...\n');
if (process.env.FAKE_MB_EMPTY === '1') {
  process.stdout.write('No results found.\n');
  process.exit(0);
}

const ARCH = '/home/u/.config/superpowers/conversation-archive/-proj';
function block(n, kind, i) {
  const overlap = kind === 'text' && i === 0 && process.env.FAKE_MB_OVERLAP === '1';
  const key = overlap ? { a: 100, b: 140, f: `${ARCH}/vec-0.jsonl` }
    : { a: 100 + i * 50, b: 140 + i * 50, f: `${ARCH}/${kind === 'vector' ? 'vec' : 'txt'}-${i}.jsonl` };
  const score = kind === 'vector' ? ` - ${60 - i}% match` : '';
  return `${n}. [-proj, 2026-10-${10 + i}]${score}\n` +
    `   "${kind} hit ${i} for the query"\n` +
    `   Lines ${key.a}-${key.b} in ${key.f} ${overlap ? '(99.9KB, 7 lines)' : '(12.3KB, 456 lines)'}\n\n`;
}
const blocks = [];
if (mode === 'vector' || mode === 'both') for (let i = 0; i < limit; i++) blocks.push(['vector', i]);
if (mode === 'text' || mode === 'both') for (let i = 0; i < limit; i++) blocks.push(['text', i]);
process.stdout.write(`Found ${blocks.length} relevant conversations:\n\n`);
blocks.forEach(([k, i], idx) => process.stdout.write(block(idx + 1, k, i)));
