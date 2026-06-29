#!/usr/bin/env python3
"""Backend Smoke Test for Pehel Neo"""
import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api/v1"
PASS = 0
FAIL = 0

def req(method, path, data=None, headers=None, expect_status=None):
    global PASS, FAIL
    url = f"{BASE_URL}{path}"
    req_obj = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req_obj.add_header(k, v)
    if data:
        req_obj.add_header('Content-Type', 'application/json')
        body = json.dumps(data).encode('utf-8')
        req_obj.data = body
    
    try:
        with urllib.request.urlopen(req_obj, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            status = resp.status
            try:
                parsed = json.loads(body) if body else None
            except:
                parsed = body
            if expect_status and status != expect_status:
                print(f"  FAIL [{status}] {method} {path} (expected {expect_status})")
                FAIL += 1
                return None
            print(f"  PASS [{status}] {method} {path}")
            PASS += 1
            return parsed
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8') if e.read() else ""
        if expect_status and e.code == expect_status:
            print(f"  PASS [{e.code}] {method} {path} (expected error)")
            PASS += 1
            return None
        print(f"  FAIL [{e.code}] {method} {path} -> {body[:200]}")
        FAIL += 1
        return None
    except Exception as e:
        print(f"  FAIL [ERR] {method} {path} -> {e}")
        FAIL += 1
        return None

print("=" * 60)
print("PEHEL NEO BACKEND SMOKE TEST")
print("=" * 60)

# --- PUBLIC ENDPOINTS ---
print("\n--- PUBLIC ENDPOINTS ---")
req("GET", "/geo/cities")
req("GET", "/geo/cities/26484efc-20a0-4a15-8686-a724b161598d")
req("GET", "/geo/cities/26484efc-20a0-4a15-8686-a724b161598d/wards")
req("GET", "/feed/")
req("GET", "/feed/trending")
req("GET", "/feed/search?q=road")
req("GET", "/feed/nearby?lat=26.4499&lng=80.3319&radius_meters=5000")
req("GET", "/issues?limit=5")

# --- CITIZEN AUTH ---
print("\n--- CITIZEN AUTH ---")
otp_resp = req("POST", "/auth/send-otp", {"phone": "+919876543210"})
if otp_resp and "otp" in otp_resp:
    otp_code = otp_resp["otp"]
    print(f"  -> OTP received: {otp_code}")
else:
    otp_code = "123456"

verify_resp = req("POST", "/auth/verify-otp", {"phone": "+919876543210", "otp": otp_code})
citizen_token = None
if verify_resp and "access_token" in verify_resp:
    citizen_token = verify_resp["access_token"]
    print(f"  -> Citizen token: {citizen_token[:20]}...")
else:
    print("  -> WARNING: Could not get citizen token")

# --- CITIZEN AUTH ENDPOINTS ---
issue_id = None
if citizen_token:
    auth_headers = {"Authorization": f"Bearer {citizen_token}"}
    print("\n--- CITIZEN AUTH ENDPOINTS ---")
    
    wards = req("GET", "/geo/cities/26484efc-20a0-4a15-8686-a724b161598d/wards")
    ward_id = wards[0]["id"] if wards else "11111111-1111-1111-1111-111111111111"
    
    issue_data = {
        "category": "roads",
        "ward_id": ward_id,
        "title": "Test road damage from smoke test",
        "description": "This is a test issue created by the smoke test script.",
        "geo_lat": 26.4499,
        "geo_lng": 80.3319,
        "location_text": "Near Kanpur Central",
        "severity": "high",
        "is_safety_risk": True,
    }
    issue_resp = req("POST", "/issues", issue_data, auth_headers)
    issue_id = issue_resp["id"] if issue_resp else None
    
    if issue_id:
        print(f"  -> Created issue: {issue_id}")
        req("GET", f"/issues/{issue_id}")
        req("GET", f"/issues/{issue_id}/timeline")
        req("POST", f"/issues/{issue_id}/support", headers=auth_headers, expect_status=400)
        req("GET", "/me/issues", headers=auth_headers)
        req("GET", "/me/supports", headers=auth_headers)
        req("POST", f"/issues/{issue_id}/comments", {"message_text": "Test comment from smoke test"}, auth_headers)
        req("GET", f"/issues/{issue_id}/comments")
        req("GET", "/me/comments", headers=auth_headers)
        req("GET", "/feed/for-you", headers=auth_headers)
        req("POST", f"/issues/{issue_id}/media/upload-url?media_type=complaint_photo&content_type=image/jpeg", headers=auth_headers)
        req("POST", f"/issues/{issue_id}/narrative")
        req("POST", f"/chat/issue/{issue_id}", {"question": "What is the status?"}, auth_headers)
        req("POST", f"/issues/{issue_id}/confirm", headers=auth_headers, expect_status=400)
        req("POST", f"/issues/{issue_id}/dispute", headers=auth_headers, expect_status=400)
    else:
        print("  -> WARNING: Could not create issue")
else:
    print("  -> SKIPPING citizen auth tests")

# --- AUTHORITY AUTH ---
print("\n--- AUTHORITY AUTH ---")
auth_login = req("POST", "/auth/authority/login", {"email": "admin@kanpur.gov.in", "password": "admin123"})
auth_token = None
if auth_login and "access_token" in auth_login:
    auth_token = auth_login["access_token"]
    print(f"  -> Authority token: {auth_token[:20]}...")
else:
    print("  -> WARNING: Could not get authority token")

# --- AUTHORITY AUTH ENDPOINTS ---
if auth_token:
    auth_headers = {"Authorization": f"Bearer {auth_token}"}
    print("\n--- AUTHORITY AUTH ENDPOINTS ---")
    req("GET", "/authority/me", headers=auth_headers)
    req("GET", "/authority/dashboard", headers=auth_headers)
    
    if issue_id:
        req("POST", f"/issues/{issue_id}/acknowledge", headers=auth_headers)
        req("POST", f"/issues/{issue_id}/visit", headers=auth_headers)
        req("POST", f"/issues/{issue_id}/start-work", headers=auth_headers)
        req("POST", f"/issues/{issue_id}/resolve", headers=auth_headers)
        
        # Now citizen can confirm
        if citizen_token:
            print("\n--- CITIZEN CONFIRMS RESOLUTION ---")
            req("POST", f"/issues/{issue_id}/confirm", headers={"Authorization": f"Bearer {citizen_token}"})
            req("GET", f"/issues/{issue_id}")
    else:
        print("  -> WARNING: No issue to test authority workflow")
else:
    print("  -> SKIPPING authority tests")

# --- SUMMARY ---
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 60)
if FAIL > 0:
    sys.exit(1)
print("ALL TESTS PASSED!")