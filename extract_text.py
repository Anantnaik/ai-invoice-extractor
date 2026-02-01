import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io


def extract_text_from_pdf(file_bytes):
    text = ""

    # Try text-based extraction first
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    if len(text.strip()) > 50:
        return text, "text_pdf"

    # Fallback to OCR
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    ocr_text = ""

    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_text += pytesseract.image_to_string(img) + "\n"

    return ocr_text, "ocr_pdf"

import re

def clean_invoice_text(text):
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove common noise patterns
    noise_patterns = [
        r'Page \d+ of \d+',
        r'Invoice generated on.*',
        r'Thank you for your business.*'
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    return text.strip()