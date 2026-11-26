"""
Tests for Frontend Demo Mode Fixtures & Public Assets.
Verifies:
- DEMO_CANDIDATE_PROFILE structure, section completeness, and skill validity
- DEMO_JOBS_LIST schema integrity across all 15 postings (score bounds, ATS sources, URLs)
- DEMO_TAILORED_RESULT ATS metrics (68 -> 91 score bump, bullet changes, sample PDF validity)
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
import fitz
import pytest


def _load_demo_data():
    """
    Loads demo fixtures from frontend_job/src/data/demoData.js.
    Uses Node if available; falls back to robust regex/JSON parser.
    """
    current_dir = Path(__file__).resolve().parent
    repo_root = current_dir.parent.parent
    js_path = repo_root / "frontend_job" / "src" / "data" / "demoData.js"

    assert js_path.exists(), f"Could not find demoData.js at {js_path}"

    if shutil.which("node"):
        uri = js_path.as_uri()
        node_script = f"import('{uri}').then(m => console.log(JSON.stringify({{profile: m.DEMO_CANDIDATE_PROFILE, jobs: m.DEMO_JOBS_LIST, tailored: m.DEMO_TAILORED_RESULT}})));"
        res = subprocess.run(["node", "--input-type=module", "-e", node_script], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return json.loads(res.stdout)

    # Fallback: parse basic structure from file text
    content = js_path.read_text(encoding="utf-8")
    return {"raw_text": content}


def test_demo_candidate_profile_schema():
    data = _load_demo_data()
    if "profile" in data:
        profile = data["profile"]
        assert "personal_info" in profile
        assert profile["personal_info"]["name"] == "Arjun Sharma"
        assert "arjun.sharma@" in profile["personal_info"]["email"]
        assert len(profile["skills"]) >= 15
        assert "Python" in profile["skills"]
        assert "FastAPI" in profile["skills"]
        assert len(profile["education"]) >= 1
        assert "DTU" in profile["education"][0]["institution"] or "Delhi" in profile["education"][0]["institution"]
        assert len(profile["experience"]) >= 1
        assert len(profile["projects"]) >= 2
    else:
        content = data["raw_text"]
        assert "export const DEMO_CANDIDATE_PROFILE" in content
        assert "Arjun Sharma" in content
        assert "FastAPI" in content
        assert "Delhi Technological University" in content


def test_demo_jobs_list_schema():
    data = _load_demo_data()
    if "jobs" in data:
        jobs = data["jobs"]
        assert len(jobs) == 15, f"Expected 15 demo jobs, found {len(jobs)}"
        for j in jobs:
            assert "id" in j and j["id"]
            assert "title" in j and j["title"]
            assert "company" in j and j["company"]
            assert "location" in j and j["location"]
            assert "apply_url" in j and j["apply_url"].startswith("http")
            assert "source" in j and j["source"] in {"ashby", "lever", "greenhouse", "remotive", "themuse", "arbeitnow"}
            assert 0 <= j["fresher_score"] <= 100
            assert 0 <= j["match_percent"] <= 100
    else:
        content = data["raw_text"]
        assert "export const DEMO_JOBS_LIST = [" in content
        # Slice between DEMO_JOBS_LIST = [ and export const DEMO_
        section = content.split("export const DEMO_JOBS_LIST = [")[1].split("export const DEMO_")[0]
        job_matches = re.findall(r"id:\s*['\"]demo-job-", section)
        assert len(job_matches) == 15


def test_demo_tailored_result_schema():
    current_dir = Path(__file__).resolve().parent
    repo_root = current_dir.parent.parent
    pdf_path = repo_root / "frontend_job" / "public" / "demo_tailored_resume.pdf"

    # 1. Verify sample PDF is deployed and readable
    assert pdf_path.exists(), f"Missing static demo PDF at {pdf_path}"
    assert pdf_path.stat().st_size > 1000, "Demo PDF is empty or corrupt"

    # Verify PDF is a valid 1-page ATS document using PyMuPDF
    doc = fitz.open(str(pdf_path))
    assert len(doc) == 1, f"Expected 1-page resume, got {len(doc)} pages"
    page_text = doc[0].get_text("text")
    assert "ARJUN SHARMA" in page_text or "Arjun Sharma" in page_text
    doc.close()

    # 2. Verify ATS metrics
    data = _load_demo_data()
    if "tailored" in data:
        tailored = data["tailored"]
        report = tailored["ats_report"]
        assert report["initial_score"] == 68
        assert report["tailored_score"] == 91
        assert report["score_delta"] == "+23 pts"
        assert len(tailored["change_log"]) >= 3
        for change in tailored["change_log"]:
            assert "original" in change
            assert "edited" in change
            assert change.get("retention_ratio", 0) >= 0.70
            assert change.get("status") == "accepted"
    else:
        content = data["raw_text"]
        assert "initial_score: 68" in content
        assert "tailored_score: 91" in content
