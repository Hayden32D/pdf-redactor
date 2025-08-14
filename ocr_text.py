import fitz  # PyMuPDF
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import sys
import os
import numpy as np




# Set path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
def preprocess_image(img):
    # Convert to grayscale
    img = img.convert("L")

    # Increase contrast
    img = ImageOps.autocontrast(img)

    # Apply a slight blur to reduce noise
    img = img.filter(ImageFilter.GaussianBlur(radius=1))

    # Apply thresholding
    img = img.point(lambda x: 0 if x < 128 else 255, '1')

    return img



def pdf_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = []

    for page_num, page in enumerate(doc):
        # Extract text normally
        text = page.get_text("text").strip()
        if text:
            full_text.append(f"--- Page {page_num + 1} ---\n{text}\n")
        else:
            # OCR for scanned page
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_preprocessed = preprocess_image(img)
            text_ocr = pytesseract.image_to_string(img_preprocessed, config=" --oem 1 --psm 3")
            full_text.append(f"--- Page {page_num + 1} (OCR) ---\n{text_ocr}\n")

    return "\n".join(full_text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        pdf_file = input("Enter path to PDF: ")

    if not os.path.exists(pdf_file):
        print("PDF file not found.")
        sys.exit(1)

    extracted_text = pdf_to_text(pdf_file)
    print(extracted_text)
