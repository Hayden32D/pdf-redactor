# PDF Redactor

A Python script to automatically **redact sensitive information** from PDF files while preserving the original formatting. This script can detect and redact:

- **Emails**
- **Phone numbers** (with optional `+1` country code)
- **Social Security Numbers (SSN)**
- **Full Names** (with introductory phrases like "My name is", "I am", etc.)
- **Dates of Birth (DOB)**

---

## Features

- Works with any PDF file.
- Redactions are applied directly on the PDF content.
- Outputs a new PDF with `_redacted` appended to the original filename.
- Simple, command-line friendly usage.

---

## Requirements

- Python 3.7+
- [PyMuPDF](https://pypi.org/project/PyMuPDF/) (`fitz` module)

Install dependencies using pip:

```bash
pip install PyMuPDF
