import hashlib
import json
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from sqlalchemy.orm import Session

from backend.database import (
    init_db,
    get_db,
    SessionLocal,
    VerifiedRegistry,
    VerificationAuditLog,
)
from backend.mock_data import seed_mock_data, hash_identifier
from backend.forensics import perform_error_level_analysis
from backend.ocr_engine import extract_document_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    init_db()
    with SessionLocal() as db:
        seed_mock_data(db)
    yield


app = FastAPI(
    title="DocuVerify AI Engine",
    description="Automated Document Verification & Image Tampering Detection Engine",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

SWAGGER_DARK_CSS = """
<style>
  body { background-color: #090d16 !important; color: #e2e8f0 !important; font-family: 'Inter', -apple-system, sans-serif !important; }
  .swagger-ui .topbar { display: none !important; }
  .swagger-ui .info .title { color: #ffffff !important; font-weight: 800 !important; }
  .swagger-ui .info p, .swagger-ui .info li { color: #94a3b8 !important; }
  .swagger-ui .scheme-container { background: #0f172a !important; box-shadow: none !important; border-bottom: 1px solid #1e293b !important; }
  .swagger-ui .opblock-tag { color: #f8fafc !important; border-bottom: 1px solid #1e293b !important; }
  .swagger-ui .opblock { background: #0f172a !important; border-color: #1e293b !important; border-radius: 12px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important; margin: 0 0 16px !important; }
  .swagger-ui .opblock .opblock-summary { border-color: transparent !important; padding: 10px 16px !important; }
  .swagger-ui .opblock .opblock-summary-method { border-radius: 6px !important; font-weight: 700 !important; }
  .swagger-ui .opblock .opblock-summary-path { color: #f1f5f9 !important; font-weight: 600 !important; }
  .swagger-ui .opblock .opblock-summary-description { color: #94a3b8 !important; }
  .swagger-ui .opblock-body { background: #090d16 !important; border-radius: 0 0 12px 12px !important; }
  .swagger-ui .opblock-description-wrapper p, .swagger-ui .opblock-title_normal { color: #cbd5e1 !important; }
  .swagger-ui table thead tr th { color: #94a3b8 !important; border-bottom: 1px solid #1e293b !important; }
  .swagger-ui .tabli button { color: #94a3b8 !important; }
  .swagger-ui .tabli.active button { color: #818cf8 !important; border-bottom: 2px solid #818cf8 !important; }
  .swagger-ui input[type=text], .swagger-ui select, .swagger-ui textarea { background: #1e293b !important; color: #f1f5f9 !important; border: 1px solid #334155 !important; border-radius: 6px !important; }
  .swagger-ui .btn { border-radius: 8px !important; color: #f1f5f9 !important; border-color: #334155 !important; background: #1e293b !important; }
  .swagger-ui .btn.execute { background: #4f46e5 !important; border-color: #6366f1 !important; color: #ffffff !important; box-shadow: 0 0 12px rgba(99, 102, 241, 0.4) !important; }
  .swagger-ui .btn.cancel { background: #be123c !important; border-color: #e11d48 !important; }
  .swagger-ui .responses-inner { background: transparent !important; }
  .swagger-ui .response-col_status { color: #818cf8 !important; }
  .swagger-ui .response-col_description { color: #cbd5e1 !important; }
  .swagger-ui .model-box { background: #0f172a !important; color: #e2e8f0 !important; }
  .swagger-ui section.models { border-color: #1e293b !important; border-radius: 12px !important; background: #0f172a !important; }
  .swagger-ui section.models h4 { color: #94a3b8 !important; border-bottom: 1px solid #1e293b !important; }
  .swagger-ui .model-title { color: #f1f5f9 !important; }
  .swagger-ui .model { color: #94a3b8 !important; }
  .swagger-ui .prop-type { color: #38bdf8 !important; }
  .swagger-ui .renderedMarkdown p { color: #94a3b8 !important; }
  .swagger-ui .loading-container { background: #090d16 !important; }
  .swagger-ui .highlight-code { background: #020617 !important; }
</style>
"""

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger API Docs",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        swagger_ui_parameters={"defaultModelsExpandDepth": -1, "syntaxHighlight.theme": "monokai"},
    )
    content = response.body.decode("utf-8")
    content = content.replace("</head>", f"{SWAGGER_DARK_CSS}</head>")
    return HTMLResponse(content=content)

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health & Info"])
def health_check():
    return {
        "service": "DocuVerify AI Engine",
        "status": "operational",
        "version": "1.0.0",
        "phase": 2,
        "capabilities": [
            "OpenCV Error Level Analysis (ELA) Tamper Forensics",
            "EasyOCR Structured Field Extraction",
            "SHA-256 Identity Hash Protection",
            "Institutional Registry Validation",
            "Audit Trail Logging",
            "Interactive Web Dashboard",
        ],
        "endpoints": {
            "verify": "POST /api/verify",
            "registry": "GET /api/records",
            "audit_logs": "GET /api/audit-logs",
            "health": "GET /api/health",
        },
    }


@app.get("/api/records", tags=["Registry"])
def get_registry_records(db: Session = Depends(get_db)):
    """List all registered mock student records."""
    records = db.query(VerifiedRegistry).all()
    return [
        {
            "id": r.id,
            "student_name": r.student_name,
            "student_id": r.student_id_raw,
            "student_id_hash": r.student_id_hash,
            "course": r.course,
            "institution": r.institution,
            "marks_or_grade": r.marks_or_grade,
            "issue_year": r.issue_year,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@app.get("/api/audit-logs", tags=["Audit"])
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve historical verification audit logs."""
    logs = (
        db.query(VerificationAuditLog)
        .order_by(VerificationAuditLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "filename": l.filename,
            "document_hash": l.document_hash,
            "detected_name": l.detected_name,
            "detected_id": l.detected_id,
            "matched_record_id": l.matched_record_id,
            "match_status": l.match_status,
            "tamper_risk_score": l.tamper_risk_score,
            "tamper_level": l.tamper_level,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
        }
        for l in logs
    ]


@app.post("/api/verify", tags=["Verification"])
async def verify_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Primary verification pipeline:
    1. Reads image file and computes SHA-256 cryptographic document hash.
    2. Runs OpenCV Error Level Analysis (ELA) for image tampering detection.
    3. Runs EasyOCR to parse structured student credentials.
    4. Compares against SHA-256 hashed database registry.
    5. Saves full audit log and returns comprehensive verdict.
    """
    if not file.content_type or not (
        file.content_type.startswith("image/")
        or file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"))
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a valid document image (JPEG, PNG, WebP).",
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read uploaded file: {str(e)}",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 1. Cryptographic Document SHA-256 Hash
    document_hash = hashlib.sha256(content).hexdigest()

    # 2. Forensic Error Level Analysis
    try:
        forensic_res = perform_error_level_analysis(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Forensic ELA processing failed: {str(e)}",
        )

    # 3. OCR Text Extraction
    try:
        ocr_res = extract_document_data(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"OCR engine processing failed: {str(e)}",
        )

    extracted_fields = ocr_res["extracted_fields"]
    detected_id = extracted_fields.get("student_id")
    detected_name = extracted_fields.get("student_name")
    detected_marks = extracted_fields.get("marks_or_grade")

    # 4. Database Registry Cross-Verification
    matched_record: Optional[VerifiedRegistry] = None
    discrepancies: List[str] = []

    if detected_id:
        id_hash = hash_identifier(detected_id)
        matched_record = (
            db.query(VerifiedRegistry)
            .filter(VerifiedRegistry.student_id_hash == id_hash)
            .first()
        )

    # Fallback to name search if ID was partially obscured or not found
    if not matched_record and detected_name:
        matched_record = (
            db.query(VerifiedRegistry)
            .filter(VerifiedRegistry.student_name.ilike(f"%{detected_name}%"))
            .first()
        )
        if matched_record and detected_id:
            discrepancies.append(
                f"Document ID '{detected_id}' did not match official ID '{matched_record.student_id_raw}'."
            )

    # 5. Field Discrepancy & Verdict Evaluation
    is_tampered = forensic_res["is_tampered"]
    tamper_score = forensic_res["tamper_risk_score"]

    if matched_record:
        # Check Name consistency
        if detected_name:
            official_name_clean = matched_record.student_name.lower().replace(".", "").strip()
            detected_name_clean = detected_name.lower().replace(".", "").strip()
            if official_name_clean not in detected_name_clean and detected_name_clean not in official_name_clean:
                discrepancies.append(
                    f"Name mismatch: Document states '{detected_name}', but registry holds '{matched_record.student_name}'."
                )

        # Check Marks consistency if present
        if detected_marks:
            clean_detected_marks = detected_marks.upper().replace(" ", "")
            clean_official_marks = matched_record.marks_or_grade.upper().replace(" ", "")
            if clean_detected_marks != clean_official_marks and clean_detected_marks not in clean_official_marks:
                discrepancies.append(
                    f"Performance metric divergence: Document specifies '{detected_marks}', whereas registry record is '{matched_record.marks_or_grade}'."
                )

        # Verdict logic
        if is_tampered or tamper_score >= 50.0:
            verdict = "TAMPERED_SUSPECT"
            is_authentic = False
            summary = (
                f"Image tampering suspected! High forensic ELA risk score of {tamper_score}% "
                f"({forensic_res['tamper_level']}). While identity matches {matched_record.student_name}, "
                f"the image exhibits localized compression inconsistencies indicative of digital modification."
            )
        elif discrepancies:
            verdict = "MISMATCH"
            is_authentic = False
            summary = (
                f"Data mismatch detected against institutional registry for ID {matched_record.student_id_raw}. "
                f"Found {len(discrepancies)} discrepancy item(s)."
            )
        else:
            verdict = "VERIFIED"
            is_authentic = True
            summary = (
                f"Document successfully verified authentic. Credentials match official record for "
                f"{matched_record.student_name} ({matched_record.student_id_raw}) with low forensic tamper risk ({tamper_score}%)."
            )
    else:
        verdict = "NOT_FOUND"
        is_authentic = False
        summary = (
            "Document credentials could not be matched with any record in the institutional verified registry."
        )
        if detected_id:
            discrepancies.append(f"Student ID '{detected_id}' not found in registry.")

    # 6. Record Audit Log
    audit_entry = VerificationAuditLog(
        filename=file.filename or "unknown_document",
        document_hash=document_hash,
        detected_name=detected_name,
        detected_id=detected_id,
        matched_record_id=matched_record.id if matched_record else None,
        match_status=verdict,
        tamper_risk_score=tamper_score,
        tamper_level=forensic_res["tamper_level"],
        details_json=json.dumps(
            {
                "discrepancies": discrepancies,
                "forensic_metrics": {
                    "mean_error": forensic_res["mean_error"],
                    "max_error": forensic_res["max_error"],
                    "std_error": forensic_res["std_error"],
                    "anomaly_ratio": forensic_res["anomaly_ratio"],
                },
                "ocr_metrics": {
                    "ocr_confidence": ocr_res["ocr_confidence"],
                    "raw_lines_count": len(ocr_res["raw_text_lines"]),
                },
            }
        ),
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)

    # 7. Assemble Structured Response
    return {
        "status": "success",
        "verification_result": {
            "verdict": verdict,
            "is_authentic": is_authentic,
            "summary": summary,
        },
        "forensic_analysis": {
            "tamper_risk_score": forensic_res["tamper_risk_score"],
            "tamper_level": forensic_res["tamper_level"],
            "is_tampered": forensic_res["is_tampered"],
            "mean_error": forensic_res["mean_error"],
            "max_error": forensic_res["max_error"],
            "std_error": forensic_res["std_error"],
            "anomaly_ratio": forensic_res["anomaly_ratio"],
            "analysis_summary": forensic_res["analysis_summary"],
            "ela_image_base64": forensic_res["ela_image_base64"],
        },
        "extracted_data": {
            "detected_id": detected_id,
            "detected_name": detected_name,
            "detected_marks": detected_marks,
            "detected_course": extracted_fields.get("course"),
            "ocr_confidence": ocr_res["ocr_confidence"],
            "raw_text_lines": ocr_res["raw_text_lines"],
        },
        "registry_comparison": {
            "matched": matched_record is not None,
            "official_record": {
                "id": matched_record.id,
                "student_name": matched_record.student_name,
                "student_id": matched_record.student_id_raw,
                "student_id_hash": matched_record.student_id_hash,
                "course": matched_record.course,
                "institution": matched_record.institution,
                "marks_or_grade": matched_record.marks_or_grade,
                "issue_year": matched_record.issue_year,
            }
            if matched_record
            else None,
            "discrepancies": discrepancies,
        },
        "audit_meta": {
            "audit_id": audit_entry.id,
            "document_hash": document_hash,
            "timestamp": audit_entry.timestamp.isoformat() if audit_entry.timestamp else None,
        },
    }


# Static Files mounting for Phase 2 Frontend Dashboard & Test Samples
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
SAMPLES_DIR = BASE_DIR / "test_samples"

# Ensure frontend directory exists before mounting
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

if SAMPLES_DIR.exists():
    app.mount("/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

