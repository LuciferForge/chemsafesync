#!/usr/bin/env python3
"""
ChemSafeSync — Executive OSHA Compliance PDF Audit Report Generator
Compiles chemical SKU inventory compliance status, revision dates, hazard classes,
and OSHA compliance scores into a formal print-ready HTML/PDF report.
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger("ComplianceReportGenerator")

REPORTS_DIR = Path("/Users/apple/Documents/products/chemsafesync/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class ComplianceReportGenerator:
    def __init__(self, reports_dir: Path = REPORTS_DIR):
        self.reports_dir = reports_dir

    def generate_html_report(self, client: Dict[str, Any], inventory: List[Dict[str, Any]], audit_summary: Dict[str, Any]) -> str:
        """
        Generates a standalone, beautifully styled HTML compliance audit report.
        """
        now_str = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")
        
        score_pct = audit_summary.get('compliance_score_pct', 0.0)
        status_color = "#00FF66" if score_pct >= 90 else "#FFCC00" if score_pct >= 75 else "#FF3366"

        sku_rows_html = []
        for item in inventory:
            st = item.get('status', 'PENDING')
            badge_class = "badge-verified" if st == 'VERIFIED' else "badge-outdated" if st == 'OUTDATED' else "badge-missing"
            
            sku_rows_html.append(f"""
            <tr>
                <td><strong>{item.get('sku')}</strong></td>
                <td>{item.get('product_name')}</td>
                <td><code>{item.get('cas_number', 'N/A')}</code></td>
                <td>{item.get('supplier_name')}</td>
                <td>{item.get('current_revision_date', 'N/A')}</td>
                <td><span class="badge {badge_class}">{st}</span></td>
            </tr>
            """)

        rows_str = "\n".join(sku_rows_html)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OSHA SDS Compliance Audit Report | {client.get('company', 'Client')}</title>
    <style>
        :root {{
            --bg: #090C15;
            --card-bg: #111625;
            --text: #F0F4F8;
            --muted: #8E9BAE;
            --border: rgba(255, 255, 255, 0.1);
            --accent-green: #00FF66;
            --accent-red: #FF3366;
            --accent-yellow: #FFCC00;
        }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 30px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .brand {{ font-size: 24px; font-weight: 800; color: var(--accent-green); }}
        .meta-info {{ font-size: 13px; color: var(--muted); text-align: right; }}
        .score-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }}
        .score-val {{ font-size: 42px; font-weight: 900; color: {status_color}; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
        .stat-box {{ background: var(--card-bg); border: 1px solid var(--border); padding: 16px; border-radius: 10px; text-align: center; }}
        .stat-label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; }}
        .stat-num {{ font-size: 22px; font-weight: 800; margin-top: 5px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        th, td {{ padding: 12px 16px; text-align: left; font-size: 13px; border-bottom: 1px solid var(--border); }}
        th {{ background: rgba(255, 255, 255, 0.05); color: var(--muted); font-weight: 700; text-transform: uppercase; font-size: 11px; }}
        .badge {{ padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
        .badge-verified {{ background: rgba(0, 255, 102, 0.15); color: var(--accent-green); border: 1px solid rgba(0, 255, 102, 0.3); }}
        .badge-outdated {{ background: rgba(255, 51, 102, 0.15); color: var(--accent-red); border: 1px solid rgba(255, 51, 102, 0.3); }}
        .badge-missing {{ background: rgba(255, 204, 0, 0.15); color: var(--accent-yellow); border: 1px solid rgba(255, 204, 0, 0.3); }}
        .footer {{ margin-top: 40px; font-size: 12px; color: var(--muted); text-align: center; border-top: 1px solid var(--border); padding-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="brand">🧪 ChemSafeSync</div>
            <div style="font-size:14px;color:var(--muted);margin-top:4px;">OSHA HCS 2012 / GHS Safety Data Sheet Audit Report</div>
        </div>
        <div class="meta-info">
            <div><strong>Company:</strong> {client.get('company', 'Client Corp')}</div>
            <div><strong>Safety Director:</strong> {client.get('name', 'N/A')}</div>
            <div><strong>Generated:</strong> {now_str}</div>
        </div>
    </div>

    <div class="score-card">
        <div>
            <h2 style="margin:0;font-size:20px;">OSHA Compliance Score</h2>
            <div style="color:var(--muted);font-size:13px;margin-top:4px;">Automated 16-Section Safety Data Sheet Verification</div>
        </div>
        <div class="score-val">{score_pct}%</div>
    </div>

    <div class="stats-grid">
        <div class="stat-box">
            <div class="stat-label">Total SKUs Ingested</div>
            <div class="stat-num">{audit_summary.get('total_skus', 0)}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Verified Up-To-Date</div>
            <div class="stat-num" style="color:var(--accent-green);">{audit_summary.get('verified_skus', 0)}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Outdated Revisions</div>
            <div class="stat-num" style="color:var(--accent-red);">{audit_summary.get('outdated_skus', 0)}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Missing / Pending</div>
            <div class="stat-num" style="color:var(--accent-yellow);">{audit_summary.get('missing_skus', 0)}</div>
        </div>
    </div>

    <h3 style="margin-bottom:15px;">Detailed Chemical SKU Inventory Audit</h3>
    <table>
        <thead>
            <tr>
                <th>SKU Code</th>
                <th>Product Chemical Name</th>
                <th>CAS Registry No.</th>
                <th>Supplier Vendor</th>
                <th>Revision Date</th>
                <th>OSHA Status</th>
            </tr>
        </thead>
        <tbody>
            {rows_str}
        </tbody>
    </table>

    <div class="footer">
        ChemSafeSync Automated Compliance Platform &middot; Verified against OSHA 29 CFR 1910.1200 Standards &middot; Confidential
    </div>
</body>
</html>
"""
        out_file = self.reports_dir / f"OSHA_Compliance_Report_{client.get('id', 1)}.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"✅ Generated OSHA Compliance Report at {out_file}")
        return str(out_file)

if __name__ == '__main__':
    rep_gen = ComplianceReportGenerator()
    dummy_client = {"id": 1, "company": "Apex Industrial Chemical Corp", "name": "Safety Director"}
    dummy_inventory = [
        {"sku": "SKU-101", "product_name": "Acetone Technical Grade", "cas_number": "67-64-1", "supplier_name": "Sigma-Aldrich", "current_revision_date": "2024-01-15", "status": "VERIFIED"},
        {"sku": "SKU-103", "product_name": "Sulfuric Acid 98%", "cas_number": "7664-93-9", "supplier_name": "McMaster-Carr", "current_revision_date": "2022-05-10", "status": "OUTDATED"}
    ]
    dummy_summary = {"total_skus": 2, "verified_skus": 1, "outdated_skus": 1, "missing_skus": 0, "compliance_score_pct": 50.0}
    path = rep_gen.generate_html_report(dummy_client, dummy_inventory, dummy_summary)
    print(f"Report Generated at: {path}")
