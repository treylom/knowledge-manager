---
name: pdf
description: PDF processing and OCR toolkit for Claude Code. Handles text extraction, table extraction, scanned PDF OCR, and PDF manipulation.
---

# PDF Processing Guide (Claude Code)

## Overview

This skill provides PDF processing capabilities for **Claude Code environments**.

> **Note for Antigravity Users**: Antigravity has built-in PDF processing capabilities. This skill is specifically for Claude Code environments where external tools are needed.

## Environment Detection

```
Claude Code → Use this skill (Marker, pytesseract, pdfplumber)
Antigravity → Use built-in PDF features (skip this skill)
```

---

## Quick Start

### Recommended: Marker PDF → Markdown (Token-Optimized)

For Claude Code / LLM workflows, **always use Marker first** to minimize token consumption (50-70% savings).

```bash
# Install once
pip install marker-pdf

# Convert single PDF to Markdown
marker_single "document.pdf" --output_format markdown --output_dir ./output

# Convert specific pages only (faster)
marker_single "document.pdf" --output_format markdown --output_dir ./output --page_range "0-5"

# High quality with LLM enhancement (requires API key)
marker_single "document.pdf" --output_format markdown --output_dir ./output --use_llm --force_ocr
```

**Marker Output**: Creates `./output/document/document.md` + images folder

### Token Savings Comparison

| Method | Tokens/Page | Use Case |
|--------|-------------|----------|
| PDF direct (Claude Vision) | ~1,500-3,000 | Quick glance |
| **Marker → Markdown** | ~850-1,000 | **Recommended for analysis** |

---

## OCR for Scanned PDFs

### Using pytesseract + pdf2image

```python
# Install: pip install pytesseract pdf2image
# Also requires Tesseract OCR installed on system

import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('scanned.pdf', dpi=300)

# OCR each page
text = ""
for i, image in enumerate(images):
    text += f"--- Page {i+1} ---\n"
    text += pytesseract.image_to_string(image, lang='kor+eng')  # Korean + English
    text += "\n\n"

print(text)
```

### Language Support

| Language | Code | Example |
|----------|------|---------|
| English | `eng` | `lang='eng'` |
| Korean | `kor` | `lang='kor'` |
| Both | `kor+eng` | `lang='kor+eng'` |
| Japanese | `jpn` | `lang='jpn'` |
| Chinese (Simplified) | `chi_sim` | `lang='chi_sim'` |

---

## Text Extraction (Digital PDFs)

### Using pdfplumber

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

### Table Extraction

```python
import pandas as pd
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # Check if table is not empty
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Combine all tables
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

---

## Image Analysis (Claude Vision)

For images within PDFs or standalone image files:

```
Step 1: Read 도구로 이미지 파일 로드
        Read("/path/to/image.png")

Step 2: Claude가 자동으로 Vision 모드로 분석
        - 다이어그램: 구조 및 관계 설명
        - 차트: 데이터 포인트 및 트렌드 추출
        - 스크린샷: UI 요소 및 텍스트 추출
        - 텍스트 이미지: OCR 수행

Step 3: 분석 결과를 노트에 포함
```

---

## PDF Manipulation

### Merge PDFs

```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

### Split PDF

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

### Extract Metadata

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
```

---

## Handling Large PDFs (10MB+)

### TOC-Based Section Processing

```
Step 1: Extract TOC/structure from PDF
        - Scan first 5 pages for Table of Contents
        - If no TOC, auto-generate from headings

Step 2: Map sections to page ranges
        - Section 1 "Introduction": pages 0-9
        - Section 2 "Methodology": pages 10-24
        - Section 3 "Results": pages 25-49
        - etc.

Step 3: Process sections in parallel with Marker
        marker_single "doc.pdf" --page_range "0-9" --output_dir ./section1
        marker_single "doc.pdf" --page_range "10-24" --output_dir ./section2
        ...

Step 4: Merge results in original order
```

### Quick Academic Paper Analysis

```python
def quick_paper_analysis(pdf_path):
    """Fast analysis of academic paper key sections"""
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)

        # Abstract + Introduction (first 3 pages)
        intro = "".join([pdf.pages[i].extract_text() or "" for i in range(min(3, total))])

        # Conclusion (last 3 pages)
        conclusion = "".join([pdf.pages[i].extract_text() or ""
                              for i in range(max(0, total-3), total)])

        return {
            'intro': intro,
            'conclusion': conclusion,
            'total_pages': total
        }
```

---

## Command-Line Tools

### pdftotext (poppler-utils)

```bash
# Extract text
pdftotext input.pdf output.txt

# Extract text preserving layout
pdftotext -layout input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt  # Pages 1-5
```

### qpdf

```bash
# Merge PDFs
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Split pages
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
```

---

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| **PDF → Markdown (LLM용)** | **Marker** | `marker_single "file.pdf" --output_format markdown` |
| **한국어 PDF** | **Marker** | Surya OCR 한국어 지원 |
| **OCR (스캔 PDF)** | **pytesseract** | Convert to image first |
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| **Large PDF (10MB+)** | **Marker** | `--page_range "0-10"` |

---

## Installation Summary

```bash
# Core (Marker - recommended)
pip install marker-pdf

# OCR (for scanned PDFs)
pip install pytesseract pdf2image
# Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract

# Text/Table extraction
pip install pdfplumber

# PDF manipulation
pip install pypdf

# Optional: pandas for table handling
pip install pandas openpyxl
```
