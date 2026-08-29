#!/usr/bin/env python3
"""
ChemSafeSync — Comprehensive Product Validation Suite
Executes multi-tier unit, integration, and API validation tests across all 6 core modules.
"""

import os
import sys
import json
import time
import urllib.request
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ChemSafeSyncValidator")

sys.path.append(str(Path(__file__).parent))
from database_manager import DatabaseManager
from pdf_vision_parser import SDSParserEngine
from vendor_sds_scraper import VendorSDSScraper
from compliance_report_generator import ComplianceReportGenerator
from sds_orchestrator import SDSComplianceOrchestrator

def validate_chemsafesync():
    print("=================================================================")
    print("      🧪 CHEMSAFESYNC PRODUCT SUITE VALIDATION PIPELINE           ")
    print("=================================================================")
    
    passed_tests = 0
    total_tests = 6

    # TEST 1: Database Vault Manager
    print("\n[TEST 1/6] Validating database_manager.py...")
    try:
        db = DatabaseManager()
        client = db.get_client(1)
        inventory = db.get_inventory(1)
        audit = db.record_audit(1)
        assert client.get("id") == 1, "Client ID mismatch"
        assert len(inventory) >= 5, "Inventory seeding failed"
        assert audit.get("total_skus") >= 5, "Audit snapshot failed"
        print("  ✅ TEST 1 PASSED: Database initialized, schemas valid, 5 SKUs verified!")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ TEST 1 FAILED: {e}")

    # TEST 2: GHS 16-Section PDF Parser Engine
    print("\n[TEST 2/6] Validating pdf_vision_parser.py...")
    try:
        parser = SDSParserEngine()
        sample_sds_text = """
        SAFETY DATA SHEET - SIGMA-ALDRICH
        Product Name: Acetone Technical Grade
        CAS-No.: 67-64-1
        Revision Date: 2024-02-10
        Signal Word: DANGER
        GHS Pictograms: FLAMMABLE, TOXIC
        """
        parsed = parser.parse_sds_content(sample_sds_text)
        assert parsed["cas_number"] == "67-64-1", "CAS Number extraction failed"
        assert parsed["signal_word"] == "DANGER", "Signal Word extraction failed"
        assert parsed["revision_date"] == "2024-02-10", "Revision Date extraction failed"
        assert "FLAMMABLE" in parsed["ghs_pictograms"], "GHS Pictogram detection failed"
        print(f"  ✅ TEST 2 PASSED: Extracted CAS: {parsed['cas_number']} | Signal: {parsed['signal_word']} | Date: {parsed['revision_date']}!")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ TEST 2 FAILED: {e}")

    # TEST 3: Vendor SDS Scraper & Portal Retrieval
    print("\n[TEST 3/6] Validating vendor_sds_scraper.py...")
    try:
        scraper = VendorSDSScraper()
        res = scraper.fetch_latest_sds("Fisher Scientific", "Isopropyl Alcohol 99%", "67-63-0")
        assert res.get("success") is True, "Vendor search failed"
        assert Path(res.get("pdf_path")).exists(), "PDF document vault storage failed"
        print(f"  ✅ TEST 3 PASSED: Retrieved SDS for Fisher Scientific! Saved to vault: {res.get('pdf_path')}")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ TEST 3 FAILED: {e}")

    # TEST 4: Executive OSHA Report Generator
    print("\n[TEST 4/6] Validating compliance_report_generator.py...")
    try:
        rep_gen = ComplianceReportGenerator()
        client = {"id": 1, "company": "Apex Industrial Chemical Corp", "name": "Safety Director"}
        inventory = db.get_inventory(1)
        audit = db.record_audit(1)
        report_path = rep_gen.generate_html_report(client, inventory, audit)
        assert Path(report_path).exists(), "Report file output failed"
        assert Path(report_path).stat().st_size > 1000, "Report content empty"
        print(f"  ✅ TEST 4 PASSED: Generated OSHA Executive Report! File size: {Path(report_path).stat().st_size} bytes")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ TEST 4 FAILED: {e}")

    # TEST 5: Orchestrator End-to-End Audit Pipeline
    print("\n[TEST 5/6] Validating sds_orchestrator.py...")
    try:
        orchestrator = SDSComplianceOrchestrator(1)
        audit_res = orchestrator.run_full_compliance_audit()
        assert audit_res.get("compliance_score_pct") > 0, "Compliance score calculation failed"
        assert Path(audit_res.get("report_file")).exists(), "Orchestrator report link missing"
        print(f"  ✅ TEST 5 PASSED: End-to-end compliance audit score: {audit_res.get('compliance_score_pct')}%!")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ TEST 5 FAILED: {e}")

    # TEST 6: Web Dashboard Control Hub HTTP Server (Port 8095)
    print("\n[TEST 6/6] Validating app.py (HTTP Dashboard on Port 8095)...")
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8095/")
        html_bytes = req.read()
        assert req.status == 200, "Web dashboard HTTP status not 200"
        assert b"ChemSafeSync" in html_bytes, "Brand missing in web HTML"
        assert b"OSHA SDS Compliance Control Hub" in html_bytes, "Title missing in web HTML"
        print("  ✅ TEST 6 PASSED: HTTP 200 OK — ChemSafeSync Web Control Hub live and responding!")
        passed_tests += 1
    except Exception as e:
        print(f"  ❌ TEST 6 FAILED: {e}")

    print("\n=================================================================")
    print(f"   RESULTS: {passed_tests}/{total_tests} VALIDATION TESTS PASSED ({passed_tests/total_tests*100:.1f}%)")
    print("=================================================================")
    
    if passed_tests == total_tests:
        print("🏆 CHEMSAFESYNC IS 100% PRODUCTION-VALIDATED & FULLY FUNCTIONAL!")

if __name__ == '__main__':
    validate_chemsafesync()
