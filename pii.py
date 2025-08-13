import re
import fitz
import os
from PIL import Image, ImageDraw, ImageEnhance
import pytesseract

class Redactor:
    @staticmethod
    def get_sensitive_data(lines):
        patterns = {
            "email": r"[\w\.\d]+@[\w\d-]+\.[\w\d.-]+",
            "phone": r"(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
            "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            "name": r"(?i)(?:My name is|I am|He is|She is|Name:|name is) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
            "dob": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b"
        }
        for line in lines:
            for pattern in patterns.values():
                for match in re.findall(pattern, line):
                    if isinstance(match, tuple):
                        yield ''.join(match)
                    else:
                        yield match

    def __init__(self, folder_path):
        self.folder_path = folder_path
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def redaction(self, pdf_path, output_folder):
        doc = fitz.open(pdf_path)
        scanned_images = []

        for page_num, page in enumerate(doc):
            page.wrap_contents()
            text = page.get_text("text")

            if text.strip():  # text-based page
                sensitive = list(self.get_sensitive_data(text.split('\n')))
                for data in sensitive:
                    areas = page.search_for(data)
                    [page.add_redact_annot(area, fill=(0,0,0)) for area in areas]
                page.apply_redactions()
            else:  # scanned page
                pix = page.get_pixmap(dpi=500)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img = img.convert("L")
                enhancer = ImageEnhance.Contrast(img)
            
                img = enhancer.enhance(2.0)
                img = img.point(lambda x: 0 if x < 160 else 255, '1')
                
                ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config='--psm 3')
                n_boxes = len(ocr_data['level'])
                for i in range(n_boxes):
                    if ocr_data['text'][i].strip():
                        print(f"{ocr_data['text'][i]}", end=' ')

                draw = ImageDraw.Draw(img)

                patterns = {
                    "email": r"[\w\.\d]+@[\w\d-]+\.[\w\d.-]+",
                    "phone": r"(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
                    "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
                    "name": r"(?i)(?:My name is|I am|He is|She is|Name:|name is) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
                    "dob": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b"
                }

                for i, word in enumerate(ocr_data['text']):
                    for pattern in patterns.values():
                        if re.findall(pattern, word):
                            x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                            draw.rectangle([x, y, x + w, y + h], fill="black")
                scanned_images.append(img)

        output_path = os.path.join(output_folder, os.path.basename(os.path.splitext(pdf_path)[0] + "_redacted.pdf"))

        # Save the PDF
        if scanned_images:
            # If there are scanned pages, merge them with text-based pages in the same PDF
            for i, img in enumerate(scanned_images):
                scanned_images[i] = img.convert("RGB")
            scanned_images[0].save(output_path, save_all=True, append_images=scanned_images[1:])
            print(f"Successfully saved scanned/redacted PDF as: {output_path}")
        else:
            doc.save(output_path)
            print(f"Successfully saved text/redacted PDF as: {output_path}")
    
    def process_folder(self):
        output_folder = os.path.join(self.folder_path, "redacted")
        os.makedirs(output_folder, exist_ok=True)

        for file_name in os.listdir(self.folder_path):
            if file_name.lower().endswith(".pdf"):
                pdf_path = os.path.join(self.folder_path, file_name)
                self.redaction(pdf_path, output_folder)


if __name__ == "__main__":
    folder_path = input("Enter the path to the PDF: ")
    redactor = Redactor(folder_path)
    redactor.process_folder()
