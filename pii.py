#imports
import re
import fitz
import os

class Redactor:
    @staticmethod

    def get_sensitive_data(lines):
        #email regex
        patterns = {
            "email": r"([\w\.\d]+\@[\w\d]+\.[\w\d]+)",
            "phone": r"(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
            "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            "name": r"(?i)(?:My name is|I am|He is|She is|Name:|name is) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)",
            "dob": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b"
        }

        for line in lines:
            for key, pattern in patterns.items():
                for match in re.findall(pattern, line):
                    if isinstance(match, tuple):
                        yield''.join(match)
                    else:
                        yield match

    def __init__(self, path):
        self.path = path

    def redaction(self):
        doc = fitz.open(self.path)

        for page in doc:
            page.wrap_contents()
            sensitive = self.get_sensitive_data(page.get_text("text").split('\n'))

            for data in sensitive:
                areas = page.search_for(data)

                [page.add_redact_annot(area, fill = (0,0,0)) for area in areas]

            page.apply_redactions()
    
        output_path = os.path.splitext(self.path)[0] + " redacted.pdf"
        doc.save(output_path)
        print("Successfully Redacted")

if __name__ == "__main__":

    path = input("Enter the path to the PDF: ")
    redactor = Redactor(path)
    redactor.redaction()



