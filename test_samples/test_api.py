import os
import sys
import time
import requests
from pathlib import Path

def detect_base_url():
    # 1. Check command line argument e.g. python test_api.py 8005
    for arg in sys.argv[1:]:
        if arg.isdigit():
            return f"http://127.0.0.1:{arg}"
        elif arg.startswith("http"):
            return arg

    # 2. Check environment variable
    env_port = os.environ.get("DOCUVERIFY_PORT")
    if env_port:
        return f"http://127.0.0.1:{env_port}"

    # 3. Probe common ports (8000, 8005) to see which is active
    for port in [8000, 8005]:
        try:
            r = requests.get(f"http://127.0.0.1:{port}/", timeout=0.5)
            if r.status_code == 200 and "DocuVerify" in r.text:
                return f"http://127.0.0.1:{port}"
        except Exception:
            pass

    return "http://127.0.0.1:8000"


BASE_URL = detect_base_url()


def wait_for_server(timeout_sec: int = 10):
    global BASE_URL
    start = time.time()
    while time.time() - start < timeout_sec:
        for port in [8000, 8005]:
            url = f"http://127.0.0.1:{port}"
            try:
                res = requests.get(f"{url}/api/health", timeout=1)
                if res.status_code == 200:
                    BASE_URL = url
                    print(f"[OK] DocuVerify server is responding at {BASE_URL}: {res.json().get('service')}")
                    return True
            except Exception:
                pass
        time.sleep(1)
    return False


def run_tests():
    print("=================================================================")
    print("   DocuVerify AI - Phase 1 Automated Verification Test Suite     ")
    print("=================================================================\n")

    if not wait_for_server():
        print(f"[ERROR] Could not connect to {BASE_URL}. Ensure uvicorn server is running.")
        sys.exit(1)

    # 1. Test Registry Endpoint
    print("\n[TEST 1] Querying /api/records (Verified Registry Database)...")
    res = requests.get(f"{BASE_URL}/api/records")
    assert res.status_code == 200, f"Failed: {res.text}"
    records = res.json()
    print(f"[PASSED] Found {len(records)} seeded student records:")
    for r in records:
        print(f"   * {r['student_name']} ({r['student_id']}) - {r['course']} | Hash: {r['student_id_hash'][:16]}...")
    assert len(records) >= 5, "Expected at least 5 seed records"

    # Samples directory
    samples_dir = Path(__file__).resolve().parent

    # 2. Test Authentic Document: Sarah Jenkins
    sarah_path = samples_dir / "sample_authentic_sarah.jpg"
    print(f"\n[TEST 2] Verifying Authentic Document: {sarah_path.name}...")
    assert sarah_path.exists(), f"Sample missing: {sarah_path}"
    with open(sarah_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/api/verify", files={"file": (sarah_path.name, f, "image/jpeg")})
    assert res.status_code == 200, f"Verify failed: {res.text}"
    data = res.json()
    verdict = data["verification_result"]["verdict"]
    tamper_score = data["forensic_analysis"]["tamper_risk_score"]
    detected_name = data["extracted_data"]["detected_name"]
    detected_id = data["extracted_data"]["detected_id"]
    print(f"   -> Verdict: {verdict}")
    print(f"   -> Detected: {detected_name} | ID: {detected_id}")
    print(f"   -> Tamper Risk Score: {tamper_score}% ({data['forensic_analysis']['tamper_level']})")
    print(f"   -> Summary: {data['verification_result']['summary']}")
    assert verdict == "VERIFIED", f"Expected VERIFIED, got {verdict}"
    assert data["verification_result"]["is_authentic"] is True
    print("[PASSED] Authentic document verified successfully with low tamper risk!")

    # 3. Test Authentic Document: David Chen
    david_path = samples_dir / "sample_authentic_david.jpg"
    print(f"\n[TEST 3] Verifying Authentic Document: {david_path.name}...")
    with open(david_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/api/verify", files={"file": (david_path.name, f, "image/jpeg")})
    assert res.status_code == 200, f"Verify failed: {res.text}"
    data = res.json()
    verdict = data["verification_result"]["verdict"]
    print(f"   -> Verdict: {verdict}")
    print(f"   -> Detected: {data['extracted_data']['detected_name']} | ID: {data['extracted_data']['detected_id']}")
    print(f"   -> Tamper Risk Score: {data['forensic_analysis']['tamper_risk_score']}%")
    assert verdict == "VERIFIED", f"Expected VERIFIED, got {verdict}"
    print("[PASSED] David Chen document verified successfully!")

    # 4. Test Tampered Document: Spliced Sarah Certificate
    tampered_path = samples_dir / "sample_tampered_sarah.jpg"
    print(f"\n[TEST 4] Verifying Spliced / Tampered Document: {tampered_path.name}...")
    with open(tampered_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/api/verify", files={"file": (tampered_path.name, f, "image/jpeg")})
    assert res.status_code == 200, f"Verify failed: {res.text}"
    data = res.json()
    verdict = data["verification_result"]["verdict"]
    tamper_score = data["forensic_analysis"]["tamper_risk_score"]
    tamper_level = data["forensic_analysis"]["tamper_level"]
    print(f"   -> Verdict: {verdict}")
    print(f"   -> Tamper Risk Score: {tamper_score}% ({tamper_level})")
    print(f"   -> Discrepancies: {data['registry_comparison']['discrepancies']}")
    print(f"   -> Summary: {data['verification_result']['summary']}")
    assert data["verification_result"]["is_authentic"] is False, "Tampered doc should NOT be authentic"
    assert verdict in ["TAMPERED_SUSPECT", "MISMATCH"], f"Expected tampering or mismatch flag, got {verdict}"
    print("[PASSED] Tampering / anomaly detected successfully!")

    # 5. Test Unregistered Document: Johnathon Doe
    unknown_path = samples_dir / "sample_unknown_student.jpg"
    print(f"\n[TEST 5] Verifying Unregistered Document: {unknown_path.name}...")
    with open(unknown_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/api/verify", files={"file": (unknown_path.name, f, "image/jpeg")})
    assert res.status_code == 200, f"Verify failed: {res.text}"
    data = res.json()
    verdict = data["verification_result"]["verdict"]
    print(f"   -> Verdict: {verdict}")
    print(f"   -> Summary: {data['verification_result']['summary']}")
    assert verdict == "NOT_FOUND", f"Expected NOT_FOUND, got {verdict}"
    assert data["verification_result"]["is_authentic"] is False
    print("[PASSED] Unregistered document correctly flagged as NOT_FOUND!")

    # 6. Test Audit Logs Endpoint
    print("\n[TEST 6] Querying /api/audit-logs...")
    res = requests.get(f"{BASE_URL}/api/audit-logs")
    assert res.status_code == 200
    logs = res.json()
    print(f"[PASSED] Retrieved {len(logs)} audit entries from SQLite:")
    for entry in logs[:4]:
        print(f"   * [{entry['timestamp']}] {entry['filename']} -> Verdict: {entry['match_status']} (Tamper: {entry['tamper_risk_score']}%)")
    assert len(logs) >= 4, "Expected at least 4 audit log entries"

    print("\n=================================================================")
    print("   ALL TESTS PASSED! DocuVerify AI Phase 1 is fully operational. ")
    print("=================================================================\n")


if __name__ == "__main__":
    run_tests()
