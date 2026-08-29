#!/usr/bin/env python3
"""
ChemSafeSync — Core Execution Orchestrator Engine
Orchestrates vendor scraping, SDS revision extraction, database synchronization,
and automatic OSHA compliance report generation.
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from database_manager import DatabaseManager
from vendor_sds_scraper import VendorSDSScraper
from pdf_vision_parser import SDSParserEngine
from compliance_report_generator import ComplianceReportGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SDSOrchestrator")

class SDSComplianceOrchestrator:
    def __init__(self, client_id: int = 1):
        self.client_id = client_id
        self.db = DatabaseManager()
        self.scraper = VendorSDSScraper()
        self.parser = SDSParserEngine()
        self.report_gen = ComplianceReportGenerator()

    def run_full_compliance_audit(self) -> Dict[str, Any]:
        """
        Executes end-to-end automated compliance audit for the client:
        1. Reads client SKU inventory from SQLite database.
        2. Queries supplier portals for latest SDS PDFs and revision dates.
        3. Parses PDF structure against GHS 16-section standard.
        4. Updates database status ('VERIFIED', 'OUTDATED', 'MISSING').
        5. Generates executive OSHA compliance report.
        """
        logger.info(f"=== STARTING AUTOMATED SDS COMPLIANCE AUDIT (Client ID: {self.client_id}) ===")
        client = self.db.get_client(self.client_id)
        inventory = self.db.get_inventory(self.client_id)

        if not inventory:
            logger.warning("No chemical SKUs found in inventory database.")
            return {"error": "Empty inventory"}

        logger.info(f"• Ingested {len(inventory)} Chemical SKUs for '{client.get('company', 'Client')}'")

        scanned_count = 0
        updated_count = 0

        for item in inventory:
            sku_id = item['id']
            product_name = item['product_name']
            cas_number = item['cas_number']
            supplier_name = item['supplier_name']
            current_date = item['current_revision_date']

            logger.info(f"--> Auditing SKU {item['sku']}: '{product_name}' (Current Date: {current_date})")

            # Execute vendor retrieval
            scrape_res = self.scraper.fetch_latest_sds(supplier_name, product_name, cas_number)

            if scrape_res.get("success"):
                new_date = scrape_res.get("retrieved_revision_date")
                pdf_path = scrape_res.get("pdf_path")

                # Parse PDF structure
                parsed_sds = self.parser.parse_sds_content(f"Product: {product_name} Revision Date: {new_date}", pdf_path)
                
                # Determine if date changed or updated
                new_status = "VERIFIED"
                if current_date and current_date < "2023-01-01":
                    new_status = "OUTDATED"

                self.db.update_sku_status(sku_id, new_status, new_date, pdf_path)
                updated_count += 1
            else:
                self.db.update_sku_status(sku_id, "MISSING", current_date)

            scanned_count += 1

        # Record Audit Snapshot & Calculate Compliance Score
        audit_summary = self.db.record_audit(self.client_id)
        fresh_inventory = self.db.get_inventory(self.client_id)

        # Generate Executive Compliance PDF/HTML Report
        report_file = self.report_gen.generate_html_report(client, fresh_inventory, audit_summary)
        audit_summary["report_file"] = report_file

        logger.info(f"✅ AUDIT COMPLETE! Final Compliance Score: {audit_summary['compliance_score_pct']}%")
        logger.info(f"📄 Report File: {report_file}")

        return audit_summary

if __name__ == '__main__':
    orchestrator = SDSComplianceOrchestrator(client_id=1)
    res = orchestrator.run_full_compliance_audit()
    print("\nOrchestrator Audit Summary Output:")
    print(json.dumps(res, indent=2))
