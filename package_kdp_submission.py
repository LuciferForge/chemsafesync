#!/usr/bin/env python3
"""
Amazon KDP Niche Print Logbook Submission & Metadata Packager
Compiles print-ready PDF assets, trim specifications, BISAC categories, and listing descriptions
for our 3 high-converting Amazon low-content niche logbooks.
"""

import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KDPPackager")

KDP_DIR = Path("/Users/apple/.gemini/antigravity/brain/caac42f7-edb6-4cb1-bd5d-34ab746d2cf7")
OUT_FILE = KDP_DIR / "kdp_submission_master_manifest.json"

KDP_BOOKS = [
    {
        "title": "ICU & Med-Surg Nurse Clinical Shift Tracker Logbook",
        "subtitle": "120-Page Comprehensive Patient Report & Shift Handoff Organizer for Registered Nurses",
        "author": "LuciferForge Healthcare Press",
        "cover_pdf": str(KDP_DIR / "kdp_nurse_logbook_cover_print_ready.pdf"),
        "trim_size": "8.5 x 11 inches",
        "page_count": 120,
        "list_price_usd": 9.99,
        "estimated_royalty_usd": 4.19,
        "bisac_category": "MEDICAL / Nursing / Clinical & Internal Medicine",
        "keywords": ["nurse shift logbook", "nursing report sheet", "ICU nurse patient tracker", "med surg handoff notebook"],
        "description": "Essential shift organizer for ICU, ER, and Med-Surg nurses. Features 120 detailed patient assessment templates."
    },
    {
        "title": "Elementary K-5 Math Speed Drills & Addition Workbook",
        "subtitle": "100 Days of Timed Tests, Single & Double Digit Math Exercises for Kids Ages 5-9",
        "author": "BrightMind Publishing",
        "cover_pdf": str(KDP_DIR / "kdp_math_workbook_cover_print_ready.pdf"),
        "trim_size": "8.5 x 11 inches",
        "page_count": 110,
        "list_price_usd": 8.99,
        "estimated_royalty_usd": 3.75,
        "bisac_category": "JUVENILE NONFICTION / Mathematics / Arithmetic",
        "keywords": ["math workbook grade 1", "timed math tests addition", "math speed drills elementary", "homeschool math practice"],
        "description": "Fun, daily timed math exercises designed to master single and double-digit addition and subtraction for grades K-5."
    },
    {
        "title": "AI Real Estate Investor Prospecting & Deal Flow Tracker",
        "subtitle": "The Ultimate Offline Logbook for Wholesalers, Landlords, and Property Acquisition Agents",
        "author": "Quant Property Press",
        "cover_pdf": str(KDP_DIR / "kdp_ai_real_estate_cover_print_ready.pdf"),
        "trim_size": "8.5 x 11 inches",
        "page_count": 120,
        "list_price_usd": 11.99,
        "estimated_royalty_usd": 5.25,
        "bisac_category": "BUSINESS & ECONOMICS / Real Estate / Investments",
        "keywords": ["real estate wholesaler logbook", "property deal flow journal", "real estate investor organizer"],
        "description": "Structured property acquisition journal for real estate investors, wholesalers, and land flippers."
    }
]

def package_kdp_manifest():
    logger.info("📦 PACKAGING AMAZON KDP NICHE LOGBOOK SUBMISSION MANIFEST...")
    
    verified_books = []
    for b in KDP_BOOKS:
        pdf_exists = Path(b["cover_pdf"]).exists()
        b["pdf_verified"] = pdf_exists
        logger.info(f"• Book: '{b['title']}' | Cover PDF Exists: {'✅ YES' if pdf_exists else '❌ NO'}")
        verified_books.append(b)

    manifest = {
        "kdp_publisher": "LuciferForge Publishing House",
        "total_titles": len(verified_books),
        "target_monthly_royalty_estimate": f"${sum(b['estimated_royalty_usd']*30 for b in verified_books):.2f}/mo (30 sales/title)",
        "titles": verified_books
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"✅ Master KDP Submission Manifest saved to {OUT_FILE}")
    return manifest

if __name__ == "__main__":
    manifest = package_kdp_manifest()
    print("\n=================================================================")
    print("      📚 AMAZON KDP PUBLISHING SUBMISSION MANIFEST              ")
    print("=================================================================")
    print(f"• Total Titles Ready for Listing: {manifest['total_titles']}")
    print(f"• Estimated Monthly Passive Royalty: {manifest['target_monthly_royalty_estimate']}")
    print("=================================================================")
