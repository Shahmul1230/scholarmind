import os
import re
import io

from pypdf import PdfReader
from PIL import Image

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import pytesseract
except Exception:
    pytesseract = None


TESSERACT_WINDOWS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def configure_tesseract():
    if not pytesseract:
        return

    if os.name == "nt" and os.path.exists(TESSERACT_WINDOWS_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_WINDOWS_PATH


def clean_line(line):
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    return line


def clean_ocr_noise(text):
    if not text:
        return ""

    noise_patterns = [
        "camscanner",
        "scanned with camscanner",
        "cam scanner",
        "scan with camscanner",
    ]

    cleaned_lines = []

    for line in text.splitlines():
        line_clean = clean_line(line)

        if not line_clean:
            continue

        lower_line = line_clean.lower()

        if any(pattern in lower_line for pattern in noise_patterns):
            continue

        cleaned_lines.append(line_clean)

    return "\n".join(cleaned_lines).strip()


def is_low_quality_extraction(text):
    if not text:
        return True

    cleaned = clean_ocr_noise(text)

    if len(cleaned.strip()) < 500:
        return True

    words = re.findall(r"[A-Za-z]{3,}", cleaned)

    if len(words) < 80:
        return True

    cam_count = text.lower().count("camscanner")

    if cam_count >= 2 and len(cleaned) < 1500:
        return True

    return False


def extract_pages_with_pypdf(file_path):
    reader = PdfReader(file_path)

    pages = []
    full_text_parts = []
    total_pages = len(reader.pages)

    for page_index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        raw_text = clean_ocr_noise(raw_text)

        lines = []

        for raw_line in raw_text.splitlines():
            cleaned = clean_line(raw_line)
            if cleaned:
                lines.append(cleaned)

        page_text = "\n".join(lines)

        pages.append({
            "page_number": page_index,
            "text": page_text,
            "lines": lines,
            "extraction_method": "pypdf",
        })

        if page_text:
            full_text_parts.append(
                f"\n\n--- Page {page_index} ---\n{page_text}"
            )

    return {
        "text": "\n".join(full_text_parts).strip(),
        "total_pages": total_pages,
        "pages": pages,
        "method": "pypdf",
    }


def ocr_page_with_pymupdf(page, dpi=220):
    if not pytesseract:
        raise RuntimeError(
            "pytesseract is not installed. Run: pip install pytesseract pillow pymupdf"
        )

    configure_tesseract()

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    pix = page.get_pixmap(
        matrix=matrix,
        alpha=False
    )

    image_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(image_bytes))

    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config="--psm 6"
    )

    return clean_ocr_noise(text)


def extract_pages_with_ocr(file_path):
    if not fitz:
        raise RuntimeError(
            "PyMuPDF is not installed. Run: pip install pymupdf"
        )

    if not pytesseract:
        raise RuntimeError(
            "pytesseract is not installed. Run: pip install pytesseract pillow"
        )

    configure_tesseract()

    document = fitz.open(file_path)

    pages = []
    full_text_parts = []
    total_pages = len(document)

    for page_index in range(total_pages):
        page = document[page_index]

        try:
            raw_text = ocr_page_with_pymupdf(page)
        except Exception as e:
            raw_text = ""
            print(f"OCR failed on page {page_index + 1}: {e}")

        lines = []

        for raw_line in raw_text.splitlines():
            cleaned = clean_line(raw_line)
            if cleaned:
                lines.append(cleaned)

        page_text = "\n".join(lines)

        pages.append({
            "page_number": page_index + 1,
            "text": page_text,
            "lines": lines,
            "extraction_method": "ocr",
        })

        if page_text:
            full_text_parts.append(
                f"\n\n--- Page {page_index + 1} ---\n{page_text}"
            )

    document.close()

    return {
        "text": "\n".join(full_text_parts).strip(),
        "total_pages": total_pages,
        "pages": pages,
        "method": "ocr",
    }


def extract_text_from_pdf(file_path):
    """
    Smart PDF extraction:
    1. First try normal text extraction using pypdf.
    2. If extracted text is empty/noisy/CamScanner-only, fallback to OCR.
    """

    normal_result = extract_pages_with_pypdf(file_path)

    if not is_low_quality_extraction(normal_result["text"]):
        return normal_result

    print("Low-quality PDF text detected. Running OCR fallback...")

    try:
        ocr_result = extract_pages_with_ocr(file_path)

        if not is_low_quality_extraction(ocr_result["text"]):
            return ocr_result

        return {
            **ocr_result,
            "warning": "OCR completed, but extracted text quality is still low.",
        }

    except Exception as e:
        return {
            **normal_result,
            "warning": f"OCR fallback failed: {str(e)}",
        }