import re
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
import easyocr

# Singleton reader instance to avoid reloading PyTorch weights on every request
_reader: Optional[easyocr.Reader] = None


def get_ocr_reader() -> easyocr.Reader:
    """Retrieve or initialize the singleton EasyOCR reader."""
    global _reader
    if _reader is None:
        # Default to CPU execution for standard compatibility; verbose=False prevents Windows cp1252 progress-bar encoding errors
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Enhance document image contrast and clarity for improved OCR text recognition.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Contrast Limited Adaptive Histogram Equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return enhanced


def extract_document_data(image_bytes: bytes) -> Dict[str, Any]:
    """
    Run EasyOCR on document image and parse structured fields:
    Name, Student ID, Marks/Grade, Course, and Institution using regex & heuristics.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    original_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if original_img is None:
        raise ValueError("Failed to decode image bytes for OCR processing.")

    processed = preprocess_for_ocr(original_img)

    reader = get_ocr_reader()
    ocr_results = reader.readtext(processed)

    raw_text_lines: List[str] = []
    confidences: List[float] = []

    for item in ocr_results:
        # item format: (bbox, text, confidence)
        if len(item) >= 3:
            text = str(item[1]).strip()
            conf = float(item[2])
        else:
            text = str(item[0]).strip()
            conf = 0.5

        if text:
            raw_text_lines.append(text)
            confidences.append(conf)

    full_text = "\n".join(raw_text_lines)
    avg_confidence = round(float(np.mean(confidences)), 2) if confidences else 0.0

    # Parse key document attributes using regular expressions
    extracted_id = parse_student_id(raw_text_lines, full_text)
    extracted_name = parse_student_name(raw_text_lines, full_text)
    extracted_marks = parse_marks_or_grade(raw_text_lines, full_text)
    extracted_course = parse_course(raw_text_lines, full_text)

    return {
        "raw_text_lines": raw_text_lines,
        "full_text": full_text,
        "ocr_confidence": avg_confidence,
        "extracted_fields": {
            "student_id": extracted_id,
            "student_name": extracted_name,
            "marks_or_grade": extracted_marks,
            "course": extracted_course,
        },
    }


def parse_student_id(lines: List[str], full_text: str) -> Optional[str]:
    """Extract standard student or certificate identifiers (e.g., STU-98421)."""
    # 1. Direct regex on STU-XXXXX pattern
    match = re.search(r"\b(STU[-_]?\d{4,6})\b", full_text, re.IGNORECASE)
    if match:
        raw = match.group(1).upper().replace("_", "-")
        return raw

    # 2. Key-value label patterns: "ID: 12345", "Student ID: STU-98421", "Roll No: 98421"
    patterns = [
        r"(?:Student\s*ID|ID\s*No|Roll\s*No|Registration\s*No|Reg\s*No|Certificate\s*No)[:.]?\s*([A-Z0-9-_]{4,12})",
        r"\bID[:\s]+([A-Z0-9-_]{4,12})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            return m.group(1).strip().upper()

    # 3. Check line-by-line
    for line in lines:
        m = re.search(r"\b([A-Z]{3}-\d{5})\b", line)
        if m:
            return m.group(1).strip().upper()

    return None


def parse_student_name(lines: List[str], full_text: str) -> Optional[str]:
    """Extract candidate recipient/student name."""
    patterns = [
        r"(?:Student\s*Name|Name\s*of\s*Student|Recipient\s*Name|Candidate\s*Name|Name)[:.]?\s*([A-Za-z\s.]{3,35})",
        r"(?:certify\s+that|conferred\s+upon|presented\s+to)\s+([A-Za-z\s.]{3,35})(?:\s+has|\s+is|\s+for|\n|,|$)",
    ]
    for pattern in patterns:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            clean_name = m.group(1).strip()
            # Filter out non-name phrases
            if len(clean_name.split()) >= 1 and not re.search(r"(degree|certificate|institute|university)", clean_name, re.I):
                return clean_name.title()

    # Heuristic: inspect line following "This is to certify that"
    for i, line in enumerate(lines):
        if re.search(r"certify\s+that", line, re.IGNORECASE) and i + 1 < len(lines):
            candidate = lines[i + 1].strip()
            if candidate and re.match(r"^[A-Za-z\s.]+$", candidate) and len(candidate.split()) <= 4:
                return candidate.title()

    return None


def parse_marks_or_grade(lines: List[str], full_text: str) -> Optional[str]:
    """Extract performance metrics (e.g. 3.92 GPA, 91.5%, Grade A+)."""
    # GPA pattern (e.g., 3.92 GPA or GPA: 3.92)
    gpa_match = re.search(r"\b(\d\.\d{1,2})\s*GPA\b", full_text, re.IGNORECASE) or re.search(
        r"GPA[:.]?\s*(\d\.\d{1,2})", full_text, re.IGNORECASE
    )
    if gpa_match:
        return f"{gpa_match.group(1)} GPA"

    # Percentage pattern (e.g., 91.5% or Marks: 91.5%)
    pct_match = re.search(r"\b(\d{1,3}(?:\.\d{1,2})?)\s*%", full_text) or re.search(
        r"(?:Marks|Percentage|Score)[:.]?\s*(\d{1,3}(?:\.\d{1,2})?%?)", full_text, re.IGNORECASE
    )
    if pct_match:
        val = pct_match.group(1).strip()
        return val if val.endswith("%") else f"{val}%"

    # Letter Grade pattern (e.g., Grade A+, Grade: A)
    grade_match = re.search(r"(?:Grade|Result)[:.]?\s*([A-F][+]?)", full_text, re.IGNORECASE)
    if grade_match:
        return f"Grade {grade_match.group(1).upper()}"

    return None


def parse_course(lines: List[str], full_text: str) -> Optional[str]:
    """Extract degree or program name."""
    patterns = [
        r"(?:Degree\s*of|Program[:.]?|Course[:.]?)\s*([A-Za-z0-9. &]{4,40})",
        r"\b(B\.Sc\.[^\n,]+|B\.Tech[^\n,]+|M\.Sc\.[^\n,]+|B\.A\.[^\n,]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            clean = m.group(1).strip()
            # Clean up trailing label if caught
            clean = re.sub(r"\b(?:Cumulative|GPA|Marks|Issue|Year).*$", "", clean, flags=re.I).strip()
            if len(clean) >= 4:
                return clean

    return None
