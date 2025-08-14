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
                    if isinstance(match, tuple):
                        yield ''.join(match)
                    else:
                        yield match

    def __init__(self, folder_path):
        self.folder_path = folder_path
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    @staticmethod
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

    def redaction(self, pdf_path, output_folder):
        doc = fitz.open(pdf_path)
        scanned_images = []

        for page_num, page in enumerate(doc):
            page.wrap_contents()
            text = page.get_text("text")

            if text.strip():  # text-based page
                sensitive = list(self.get_sensitive_data(text.split('\n')))

                #print stuff
                print(f"\n[Page {page_num + 1}] Found PII in text-based page:")
                for data in sensitive:
                    print(f"  - {data}")


                for data in sensitive:
                    areas = page.search_for(data)
                    [page.add_redact_annot(area, fill=(0,0,0)) for area in areas]
                page.apply_redactions()
            else:  # scanned page
                pix = page.get_pixmap(dpi=500)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                img_preprocessed = Redactor.preprocess_image(img)
                ocr_data = pytesseract.image_to_data(img_preprocessed, output_type=pytesseract.Output.DICT, config='--oem 1 --psm 3')

                draw = ImageDraw.Draw(img)

                patterns = {
                    "email": r"[\w\.\d]+@[\w\d-]+\.[\w\d.-]+",
                    "phone": r"(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
                    "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
                    "name": r"(?i)(?:My name is|I am|He is|She is|Name:|name is|dear,|mr.|Hello,|Hello|Salutations) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
                    "dob": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b",
                    "address": r"\b\d{1,6}\s+[A-Za-z0-9.,'’\- ]+\s*,?\s*[A-Za-z\- ]+\s*,?\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)?\s+\d{5}(?:-\d{4})?\b"

                }



                # Combine grouped lines into blocks of text
                grouped_lines = []
                current_group = []
                last_y = None

                for i in range(len(ocr_data['text'])):
                    word = ocr_data['text'][i]
                    y = ocr_data['top'][i]
                    if word.strip():
                        if last_y is None or abs(y - last_y) < 50:  # You can tweak this threshold
                            current_group.append((word, i))
                        else:
                            grouped_lines.append(current_group)
                            current_group = [(word, i)]
                        last_y = y

                if current_group:
                    grouped_lines.append(current_group)

                combined_blocks = []
                block = []
                
                for group in grouped_lines:
                    group_y = min([ocr_data['top'][i] for _, i in group])
                    if last_y is None or abs(group_y - last_y) < 80:  # Adjust threshold as needed
                        block.extend(group)
                    else:
                        combined_blocks.append(block)
                        block = group
                    last_y = group_y

                if block:
                    combined_blocks.append(block)

                # Apply regex to combined blocks
                for block in combined_blocks:
                    block_text = ' '.join([w for w, _ in block])
                    for pattern in patterns.values():
                        matches = re.findall(pattern, block_text)
                        for match in matches:
                            match_str = ''.join(match) if isinstance(match, tuple) else match
                            match_words = match_str.split()
                            for w, i in block:
                                if w in match_words:
                                    x, y, w_box, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                                    draw.rectangle([x, y, x + w_box, y + h], fill="black")


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
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else: 
        folder_path = input("Enter the path to the PDF: ")
    redactor = Redactor(folder_path)
    redactor.process_folder()