# PDF Redactor

A Python tool for **automatically redacting sensitive information** from PDF files, including **emails, phone numbers, SSNs, names, and dates of birth**. Works with both **text-based PDFs** and **scanned/image PDFs** using OCR.

---

## Features

- Detects and redacts:
  - Emails (including domains with hyphens)
  - Phone numbers (US format)
  - Social Security Numbers (SSNs)
  - Names (using simple keyword patterns)
  - Dates of birth
- Supports both **text-based PDFs** and **scanned PDFs**
- Uses **Tesseract OCR** for scanned pages
- Preprocesses images with contrast enhancement and thresholding for better detection
- Saves all redacted PDFs to a ``** folder** inside the source folder
- Preserves original PDF formatting for text-based pages

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/pdf-redactor.git
cd pdf-redactor
```

2. Install dependencies (Python 3.8+ recommended):

```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:

- Windows: [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)
- Make sure to set the path in your script:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## Usage

1. Place your PDF files in a folder.
2. Run the script:

```bash
python pii.py
```

3. Enter the path to the folder containing PDFs when prompted.
4. The script will process all PDFs and save redacted versions to a `redacted` subfolder.

---

## Example

```
Enter the path to the PDF folder: C:\Users\HDouglas\Documents\PDFs
Successfully saved scanned/redacted PDF as: C:\Users\HDouglas\Documents\PDFs\redacted\example_redacted.pdf
```

---

## Notes / Tips

- The OCR may not detect extremely small, rotated, or distorted text perfectly. Adjust `--psm` or preprocessing if needed.
- Emails with hyphens in the domain are now correctly detected.
- For large PDFs or high-resolution images, processing may take a few minutes.

---

## Dependencies

- [PyMuPDF (fitz)](https://pypi.org/project/PyMuPDF/) — PDF manipulation
- [Pillow](https://pypi.org/project/Pillow/) — Image processing
- [pytesseract](https://pypi.org/project/pytesseract/) — OCR engine
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — External OCR binary

---

## License

MIT License – see LICENSE file for details.

