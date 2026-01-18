---
name: pdf
description: PDF processing skill for Korean path PDFs. Use this skill when PDF path contains Korean characters.
license: Proprietary. LICENSE.txt has complete terms
---

# PDF Processing Guide

## 🛑 CRITICAL: When to Use This Skill vs Read Tool

**Claude Code의 알려진 버그**: 한글 경로에서 Read 도구가 UTF-8 에러 발생 (GitHub Issue #18285, #14392)

| PDF 경로 유형 | 처리 방법 |
|-------------|----------|
| **영어만 경로** | **Read 도구로 직접 읽기** ✅ (이 스킬 필요 없음) |
| **한글 포함 경로** | **이 스킬(/pdf) 사용** → marker_single로 변환 |

### 예시

```
✅ 영어 경로 - Read 사용:
   Read("C:\Users\user\AI\document.pdf")

✅ 한글 경로 - /pdf 스킬 사용:
   /pdf "C:\Users\user\바탕 화면\문서.pdf"
```

**⚠️ 한글 경로에서 Read 직접 사용 금지! UTF-8 에러 발생!**

---

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see reference.md. If you need to fill out a PDF form, read forms.md and follow its instructions.

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

### Legacy: pypdf (for programmatic PDF manipulation)

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python Libraries

### pypdf - Basic Operations

#### Merge PDFs
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

#### Split PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Extract Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

#### Rotate Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # Rotate 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - Text and Table Extraction

#### Extract Text with Layout
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Extract Tables
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### Advanced Table Extraction
```python
import pandas as pd

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

### reportlab - Create PDFs

#### Basic PDF Creation
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# Add text
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# Add a line
c.line(100, height - 140, 400, height - 140)

# Save
c.save()
```

#### Create PDF with Multiple Pages
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Add content
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# Page 2
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# Build PDF
doc.build(story)
```

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
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Rotate pages
qpdf input.pdf output.pdf --rotate=+90:1  # Rotate page 1 by 90 degrees

# Remove password
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk (if available)
```bash
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

## Common Tasks

### Extract Text from Scanned PDFs
```python
# Requires: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('scanned.pdf')

# OCR each page
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Add Watermark
```python
from pypdf import PdfReader, PdfWriter

# Create watermark (or load existing)
watermark = PdfReader("watermark.pdf").pages[0]

# Apply to all pages
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### Extract Images
```bash
# Using pdfimages (poppler-utils)
pdfimages -j input.pdf output_prefix

# This extracts all images as output_prefix-000.jpg, output_prefix-001.jpg, etc.
```

### Password Protection
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Add password
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Handling Large PDFs (10MB+)

When PDF files are too large for direct processing, use this 2-step selective approach:

### Step 1: Extract Text and Generate Structure Map

```python
import pdfplumber
import re

def extract_pdf_structure(pdf_path):
    """Extract TOC and section structure from large PDF"""
    output_path = pdf_path.replace('.pdf', '_extracted.txt')
    structure = []

    with pdfplumber.open(pdf_path) as pdf:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                f.write(f"--- Page {i+1} ---\n{text}\n\n")

                # Detect section headings (numbered or # prefixed)
                headings = re.findall(r'^(?:\d+\.?\s+|#+\s*)([A-Z][^.!?\n]{5,80})$',
                                     text, re.MULTILINE)
                for h in headings:
                    structure.append({'page': i+1, 'heading': h.strip()})

    return structure, output_path

# Usage
structure, txt_path = extract_pdf_structure("large_paper.pdf")
print("Document Structure:")
for item in structure:
    print(f"  Page {item['page']}: {item['heading']}")
```

### Step 2: Selective Section Reading

```python
def read_pdf_section(pdf_path, start_page, end_page):
    """Read specific page range from PDF"""
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for i in range(start_page - 1, min(end_page, len(pdf.pages))):
            text += f"--- Page {i+1} ---\n"
            text += pdf.pages[i].extract_text() or ""
            text += "\n\n"
    return text

def read_pdf_by_section(pdf_path, section_name, structure):
    """Read specific section based on heading"""
    for i, item in enumerate(structure):
        if section_name.lower() in item['heading'].lower():
            start = item['page']
            end = structure[i+1]['page'] if i+1 < len(structure) else start + 5
            return read_pdf_section(pdf_path, start, end)
    return None

# Usage examples
# Read Abstract and Introduction (typically first 5 pages)
intro = read_pdf_section("paper.pdf", 1, 5)

# Read specific section
methodology = read_pdf_by_section("paper.pdf", "Methodology", structure)
```

### Step 3: Chunked Processing for Full Analysis

```python
def process_pdf_in_chunks(pdf_path, chunk_size=10):
    """Process large PDF in manageable chunks"""
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        chunks = []

        for start in range(0, total_pages, chunk_size):
            end = min(start + chunk_size, total_pages)
            chunk_text = ""
            for i in range(start, end):
                chunk_text += pdf.pages[i].extract_text() or ""
            chunks.append({
                'pages': f"{start+1}-{end}",
                'text': chunk_text
            })

    return chunks

# Process each chunk sequentially
chunks = process_pdf_in_chunks("large_paper.pdf", chunk_size=10)
for chunk in chunks:
    print(f"Processing pages {chunk['pages']}...")
    # Analyze chunk['text'] here
```

### Academic Paper Quick Analysis Pattern

For research papers, prioritize these sections:
1. **Abstract** (Page 1) - Summary of findings
2. **Introduction** (Pages 1-3) - Context and motivation
3. **Conclusion** (Last 2-3 pages) - Key takeaways
4. **Figures/Tables** - Extract and analyze separately

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
            'title': pdf.pages[0].extract_text()[:200] if pdf.pages else "",
            'intro': intro,
            'conclusion': conclusion,
            'total_pages': total
        }
```

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| **PDF → Markdown (LLM용)** | **Marker** | `marker_single "file.pdf" --output_format markdown` |
| **한국어 PDF** | **Marker** | Surya OCR 한국어 지원 |
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs | reportlab | Canvas or Platypus |
| Command line merge | qpdf | `qpdf --empty --pages ...` |
| OCR scanned PDFs | pytesseract | Convert to image first |
| Fill PDF forms | pdf-lib or pypdf (see forms.md) | See forms.md |
| **Large PDF (10MB+)** | **Marker** | `marker_single --page_range "0-10"` |

## Next Steps

- For advanced pypdfium2 usage, see reference.md
- For JavaScript libraries (pdf-lib), see reference.md
- If you need to fill out a PDF form, follow the instructions in forms.md
- For troubleshooting guides, see reference.md
