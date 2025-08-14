import re
import fitz
import os
from PIL import Image, ImageDraw, ImageEnhance, ImageOps, ImageFilter
import pytesseract
import sys
import io

class Redactor:
    @staticmethod
    def get_sensitive_data(lines):
        """
        Scan lines of text for sensitive information using regex patterns.
        Yields each match found.
        """
        patterns = {
            "email": r"[\w\.\d]+@[\w\d-]+\.[\w\d.-]+",
            "phone": r"(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
            "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            "name": r"(?i)(?:My name is|I am|He is|She is|Name:|name is) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
            "dob": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b",
            "address": r"\b\d{1,6}\s+[A-Za-z0-9.,'’\- ]+\s*,?\s*[A-Za-z\- ]+\s*,?\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)?\s+\d{5}(?:-\d{4})?\b"
        }
        for line in lines:
            for pattern in patterns.values():
                for match in re.findall(pattern, line):
                    # Handle tuple matches from regex groups
                    if isinstance(match, tuple):
                        yield ''.join(match)
                    else:
                        yield match

    def __init__(self, folder_path):
        """
        Initialize the redactor with the folder containing PDFs.
        """
        self.folder_path = folder_path
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    @staticmethod
    def preprocess_image(img):
        """
        Preprocess scanned images for better OCR accuracy:
        - Convert to grayscale
        - Auto-contrast
        - Slight blur for noise reduction
        - Threshold to black/white
        """
        img = img.convert("L")
        img = ImageOps.autocontrast(img)
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        return img

    def redaction(self, pdf_path, output_folder):
        """
        Perform PII redaction on a single PDF file.
        Handles both text-based and scanned pages.
        """
        doc = fitz.open(pdf_path)
        scanned_images = []

        for page_num, page in enumerate(doc):
            page.wrap_contents()
            text = page.get_text("text")

            if text.strip():  # Text-based page
                sensitive = list(self.get_sensitive_data(text.split('\n')))

                # Debug print: show found PII
                print(f"\n[Page {page_num + 1}] Found PII in text-based page:")
                for data in sensitive:
                    print(f"  - {data}")

                # Redact matched text
                for data in sensitive:
                    areas = page.search_for(data)
                    [page.add_redact_annot(area, fill=(0,0,0)) for area in areas]
                page.apply_redactions()

            else:  # Scanned image page
                pix = page.get_pixmap(dpi=500)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Preprocess for OCR
                img_preprocessed = Redactor.preprocess_image(img)
                ocr_data = pytesseract.image_to_data(
                    img_preprocessed, 
                    output_type=pytesseract.Output.DICT, 
                    config='--oem 1 --psm 3'
                )

                draw = ImageDraw.Draw(img)

                # Same regex patterns as text pages but with extra triggers
                patterns = {
                    "email": r"[\w\.\d]+@[\w\d-]+\.[\w\d.-]+",
                    "phone": r"(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
                    "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
                    "name": r"(?i)(?:My name is|I am|He is|She is|Name:|name is|dear,|mr.|Hello,|Hello|Salutations) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
                    "dob": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b",
                    "address": r"\b\d{1,6}\s+[A-Za-z0-9.,'’\- ]+\s*,?\s*[A-Za-z\- ]+\s*,?\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)?\s+\d{5}(?:-\d{4})?\b"
                }

                # Group OCR words into lines
                grouped_lines = []
                current_group = []
                last_y = None

                for i in range(len(ocr_data['text'])):
                    word = ocr_data['text'][i]
                    y = ocr_data['top'][i]
                    if word.strip():
                        if last_y is None or abs(y - last_y) < 50:
                            current_group.append((word, i))
                        else:
                            grouped_lines.append(current_group)
                            current_group = [(word, i)]
                        last_y = y

                if current_group:
                    grouped_lines.append(current_group)

                # Combine close groups into text blocks
                combined_blocks = []
                block = []
                for group in grouped_lines:
                    group_y = min([ocr_data['top'][i] for _, i in group])
                    if last_y is None or abs(group_y - last_y) < 80:
                        block.extend(group)
                    else:
                        combined_blocks.append(block)
                        block = group
                    last_y = group_y

                if block:
                    combined_blocks.append(block)

                # Search each block for sensitive data
                for block in combined_blocks:
                    block_text = ' '.join([w for w, _ in block])
                    for pattern in patterns.values():
                        matches = re.findall(pattern, block_text)
                        for match in matches:
                            match_str = ''.join(match) if isinstance(match, tuple) else match
                            match_words = match_str.split()
                            # Black out matched words
                            for w, i in block:
                                if w in match_words:
                                    x, y, w_box, h = (
                                        ocr_data['left'][i], 
                                        ocr_data['top'][i], 
                                        ocr_data['width'][i], 
                                        ocr_data['height'][i]
                                    )
                                    draw.rectangle([x, y, x + w_box, y + h], fill="black")

                scanned_images.append(img)

        # Determine output path
        output_path = os.path.join(output_folder, os.path.basename(os.path.splitext(pdf_path)[0] + "_redacted.pdf"))

        # Save output PDF
        if scanned_images:
            for i, img in enumerate(scanned_images):
                scanned_images[i] = img.convert("RGB")
            scanned_images[0].save(output_path, save_all=True, append_images=scanned_images[1:])
            print(f"Successfully saved scanned/redacted PDF as: {output_path}")
        else:
            doc.save(output_path)
            print(f"Successfully saved text/redacted PDF as: {output_path}")
    
    def process_folder(self):
        """
        Process all PDFs in the given folder and save redacted versions
        to a 'redacted' subfolder.
        """
        output_folder = os.path.join(self.folder_path, "redacted")
        os.makedirs(output_folder, exist_ok=True)

        for file_name in os.listdir(self.folder_path):
            if file_name.lower().endswith(".pdf"):
                pdf_path = os.path.join(self.folder_path, file_name)
                self.redaction(pdf_path, output_folder)


if __name__ == "__main__":
    # Get folder path from command line or user input
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else: 
        folder_path = input("Enter the path to the PDF: ")
    redactor = Redactor(folder_path)
    redactor.process_folder()
