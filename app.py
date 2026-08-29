#!/usr/bin/env python3
"""
ChemSafeSync — Production Web Control Hub & API Dashboard
Provides a clean, ultra-responsive Web Dashboard for Safety Directors to manage SKUs,
run automated SDS compliance audits, and download OSHA compliance reports.
"""

import os
import json
import logging
from flask import Flask, render_template_string, jsonify, request, send_file
from pathlib import Path

from database_manager import DatabaseManager
from sds_orchestrator import SDSComplianceOrchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ChemSafeSyncWeb")

app = Flask(__name__)
db = DatabaseManager()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🧪 ChemSafeSync | OSHA SDS Compliance Control Hub</title>
  <style>
    :root {
      --bg: #090C15;
      --card: #111625;
      --border: rgba(255, 255, 255, 0.08);
      --text: #F0F4F8;
      --muted: #8E9BAE;
      --accent-green: #00FF66;
      --accent-red: #FF3366;
      --accent-blue: #00E5FF;
      --accent-yellow: #FFCC00;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg); color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 24px; max-width: 1200px; margin: 0 auto;
    }
    .header {
      display: flex; justify-content: space-between; align-items: center;
      padding-bottom: 20px; border-bottom: 1px solid var(--border); margin-bottom: 24px;
    }
    .brand { font-size: 22px; font-weight: 800; color: var(--accent-green); display: flex; align-items: center; gap: 10px; }
    .status-badge {
      background: rgba(0, 255, 102, 0.15); color: var(--accent-green);
      padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700;
      border: 1px solid rgba(0, 255, 102, 0.3); display: flex; align-items: center; gap: 6px;
    }
    .dot { width: 8px; height: 8px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 8px var(--accent-green); }
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
    .card { background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 14px; }
    .label { font-size: 12px; color: var(--muted); font-weight: 600; text-transform: uppercase; margin-bottom: 6px; }
    .val { font-size: 28px; font-weight: 800; color: #FFF; }
    .sub { font-size: 12px; color: var(--accent-green); font-weight: 700; margin-top: 4px; }
    
    .action-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .btn {
      padding: 12px 20px; border-radius: 10px; font-weight: 800; font-size: 13px;
      border: none; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px;
    }
    .btn-primary { background: linear-gradient(135deg, #00FF66, #00B347); color: #000; box-shadow: 0 4px 15px rgba(0, 255, 102, 0.3); }
    .btn-secondary { background: rgba(255, 255, 255, 0.08); color: var(--text); border: 1px solid var(--border); }
    .btn:hover { opacity: 0.9; transform: translateY(-1px); }

    table { width: 100%; border-collapse: collapse; background: var(--card); border-radius: 14px; overflow: hidden; border: 1px solid var(--border); }
    th, td { padding: 14px 18px; text-align: left; font-size: 13px; border-bottom: 1px solid var(--border); }
    th { background: rgba(255, 255, 255, 0.03); color: var(--muted); font-weight: 700; text-transform: uppercase; font-size: 11px; }
    
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; text-transform: uppercase; }
    .badge-verified { background: rgba(0, 255, 102, 0.15); color: var(--accent-green); border: 1px solid rgba(0, 255, 102, 0.3); }
    .badge-outdated { background: rgba(255, 51, 102, 0.15); color: var(--accent-red); border: 1px solid rgba(255, 51, 102, 0.3); }
    .badge-pending { background: rgba(255, 204, 0, 0.15); color: var(--accent-yellow); border: 1px solid rgba(255, 204, 0, 0.3); }
  </style>
</head>
<body>

  <div class="header">
    <div class="brand">🧪 ChemSafeSync</div>
    <div class="status-badge"><span class="dot"></span> OSHA COMPLIANCE MONITOR ACTIVE</div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="label">OSHA Score</div>
      <div class="val" style="color: var(--accent-green);">{{ audit.compliance_score_pct }}%</div>
      <div class="sub">Verified Compliant</div>
    </div>
    <div class="card">
      <div class="label">Total Chemical SKUs</div>
      <div class="val">{{ audit.total_skus }}</div>
      <div class="sub" style="color: var(--accent-blue);">Active Inventory</div>
    </div>
    <div class="card">
      <div class="label">Verified Up-To-Date</div>
      <div class="val" style="color: var(--accent-green);">{{ audit.verified_skus }}</div>
      <div class="sub">16-Section Standardized</div>
    </div>
    <div class="card">
      <div class="label">Outdated Revisions</div>
      <div class="val" style="color: var(--accent-red);">{{ audit.outdated_skus }}</div>
      <div class="sub" style="color: var(--accent-red);">Requires Update</div>
    </div>
  </div>

  <div id="toastBanner" style="display:none;background:rgba(0,255,102,0.15);border:1px solid var(--accent-green);color:var(--accent-green);padding:12px 18px;border-radius:10px;margin-bottom:20px;font-weight:700;font-size:13px;"></div>

  <div class="action-bar">
    <h3 style="font-size: 18px; font-weight: 700;">Chemical Inventory & Safety Data Sheets (SDSs)</h3>
    <div style="display:flex; gap:10px; flex-wrap:wrap;">
      <button class="btn btn-primary" onclick="openCheckoutModal()" style="background:linear-gradient(135deg, #00FF66, #00B347);color:#000;box-shadow:0 0 15px rgba(0,255,102,0.4);">💳 Start 14-Day Free Trial ($299/mo)</button>
      <label class="btn btn-secondary" style="cursor:pointer;">
        📤 Upload CSV Inventory
        <input type="file" id="csvFileInput" accept=".csv" style="display:none;" onchange="uploadCSV(this)">
      </label>
      <button class="btn btn-secondary" style="border-color:var(--accent-red);color:var(--accent-red);" onclick="loadFailingScenario()">⚠️ Load Failing Test Scenario (33.3% Score)</button>
      <button class="btn btn-secondary" style="border-color:var(--accent-green);color:var(--accent-green);" onclick="loadCompliantScenario()">🟢 Reset Compliant Scenario (100% Score)</button>
      <button class="btn btn-secondary" onclick="runAudit()">🔄 Run Live Vendor Audit</button>
      <a href="/report" target="_blank" class="btn btn-primary" style="text-decoration:none;background:rgba(255,255,255,0.08);color:#fff;border:1px solid var(--border);">📄 Download Executive Audit PDF</a>
    </div>
  </div>

  <!-- Stripe / Polar Subscription Checkout Modal -->
  <div id="checkoutModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:999;display:none;justify-content:center;align-items:center;">
    <div style="background:var(--card);border:1px solid var(--accent-green);padding:30px;border-radius:16px;max-width:500px;width:90%;box-shadow:0 0 30px rgba(0,255,102,0.2);position:relative;">
      <h2 style="color:var(--accent-green);font-size:22px;margin-bottom:10px;">🧪 ChemSafeSync Enterprise Pro</h2>
      <p style="font-size:14px;color:var(--muted);margin-bottom:20px;">Automated OSHA SDS revision monitoring for 500+ SKUs, vendor API sync, and monthly PDF compliance audits.</p>
      
      <div style="background:rgba(255,255,255,0.03);padding:16px;border-radius:10px;margin-bottom:20px;border:1px solid var(--border);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span style="font-weight:700;font-size:15px;">Monthly Plan</span>
          <span style="font-weight:800;font-size:20px;color:var(--accent-green);">$299 / mo</span>
        </div>
        <div style="font-size:12px;color:var(--accent-blue);">Includes 14-Day Full Access Free Trial &bull; Cancel Anytime</div>
      </div>

      <div style="display:flex;flex-direction:column;gap:12px;">
        <a href="https://buy.stripe.com/test_chemsafesync_299" target="_blank" onclick="alert('✅ Redirecting to Secure Stripe Checkout (14-Day Free Trial)!')" class="btn btn-primary" style="justify-content:center;padding:14px;font-size:15px;text-decoration:none;">💳 Pay via Stripe (Credit / Debit Card)</a>
        <button class="btn btn-secondary" onclick="closeCheckoutModal()" style="justify-content:center;padding:12px;">Cancel</button>
      </div>
    </div>
  </div>

  <script>
    function openCheckoutModal() { document.getElementById('checkoutModal').style.display = 'flex'; }
    function closeCheckoutModal() { document.getElementById('checkoutModal').style.display = 'none'; }
  </script>

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
      {% for item in inventory %}
      <tr>
        <td><strong>{{ item.sku }}</strong></td>
        <td>{{ item.product_name }}</td>
        <td><code style="color: var(--accent-blue);">{{ item.cas_number or 'N/A' }}</code></td>
        <td>{{ item.supplier_name }}</td>
        <td>{{ item.current_revision_date or 'N/A' }}</td>
        <td>
          {% if item.status == 'VERIFIED' %}
            <span class="badge badge-verified">VERIFIED</span>
          {% elif item.status == 'OUTDATED' %}
            <span class="badge badge-outdated">OUTDATED</span>
          {% else %}
            <span class="badge badge-pending">{{ item.status }}</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <script>
    function loadFailingScenario() {
      if(!confirm("Load Non-Compliant test dataset with 10 outdated 2018-2021 SDS sheets?")) return;
      fetch('/api/load_failing_dataset', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
          alert('⚠️ FAILING SCENARIO LOADED!\nTotal SKUs: ' + data.total_skus + '\nOutdated SKUs: ' + data.outdated_skus + '\nOSHA Compliance Score: ' + data.compliance_score_pct + '%');
          location.reload();
        });
    }

    function loadCompliantScenario() {
      fetch('/api/load_compliant_dataset', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
          alert('🟢 COMPLIANT 50-SKU DATASET RESTORED!\nOSHA Compliance Score: ' + data.compliance_score_pct + '%');
          location.reload();
        });
    }

    function uploadCSV(input) {
      const file = input.files[0];
      if(!file) return;
      const formData = new FormData();
      formData.append('file', file);
      
      fetch('/api/upload_csv', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
          alert('✅ CSV Inventory Uploaded Successfully!\nLoaded ' + data.total_skus + ' SKUs.\nNew Compliance Score: ' + data.compliance_score_pct + '%');
          location.reload();
        })
        .catch(err => alert('Upload error: ' + err));
    }

    function runAudit() {
      const btn = document.querySelector('.btn-secondary');
      const toast = document.getElementById('toastBanner');
      
      btn.disabled = true;
      btn.innerText = '⚡ Auditing SKUs...';
      toast.style.display = 'block';
      toast.style.background = 'rgba(0, 229, 255, 0.15)';
      toast.style.borderColor = 'var(--accent-blue)';
      toast.style.color = 'var(--accent-blue)';
      toast.innerHTML = '⏳ <strong>AUDIT IN PROGRESS:</strong> Parsing GHS 16-section SDS files across inventory...';

      fetch('/api/audit', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
          btn.disabled = false;
          btn.innerText = '🔄 Run Live Vendor Audit';
          toast.style.background = data.compliance_score_pct < 80 ? 'rgba(255, 51, 102, 0.15)' : 'rgba(0, 255, 102, 0.15)';
          toast.style.borderColor = data.compliance_score_pct < 80 ? 'var(--accent-red)' : 'var(--accent-green)';
          toast.style.color = data.compliance_score_pct < 80 ? 'var(--accent-red)' : 'var(--accent-green)';
          toast.innerHTML = '✅ <strong>AUDIT COMPLETE!</strong> OSHA Score: <strong>' + data.compliance_score_pct + '%</strong> | Outdated SKUs: <strong>' + data.outdated_skus + '</strong>';
          
          const valCards = document.querySelectorAll('.val');
          if (valCards.length >= 4) {
            valCards[0].innerText = data.compliance_score_pct + '%';
            valCards[1].innerText = data.total_skus;
            valCards[2].innerText = data.verified_skus;
            valCards[3].innerText = data.outdated_skus;
          }
        });
    }
  </script>

</body>
</html>
"""

@app.route("/")
def index():
    client = db.get_client(1)
    inventory = db.get_inventory(1)
    audit = db.record_audit(1)
    return render_template_string(DASHBOARD_HTML, client=client, inventory=inventory, audit=audit)

@app.route("/api/audit", methods=["POST"])
def api_audit():
    orchestrator = SDSComplianceOrchestrator(client_id=1)
    res = orchestrator.run_full_compliance_audit()
    return jsonify(res)

@app.route("/api/load_failing_dataset", methods=["POST"])
def api_load_failing():
    count = db.load_failing_sample_dataset(1)
    audit = db.record_audit(1)
    return jsonify(audit)

@app.route("/api/load_compliant_dataset", methods=["POST"])
def api_load_compliant():
    count = db.load_compliant_sample_dataset(1)
    audit = db.record_audit(1)
    return jsonify(audit)

@app.route("/api/upload_csv", methods=["POST"])
def api_upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    csv_str = file.read().decode('utf-8', errors='ignore')
    count = db.replace_inventory_from_csv(1, csv_str)
    audit = db.record_audit(1)
    return jsonify(audit)

@app.route("/report")
def download_report():
    client = db.get_client(1)
    inventory = db.get_inventory(1)
    audit = db.record_audit(1)
    from compliance_report_generator import ComplianceReportGenerator
    rep_gen = ComplianceReportGenerator()
    path = rep_gen.generate_html_report(client, inventory, audit)
    return send_file(path)

if __name__ == "__main__":
    logger.info("⚡ Launching ChemSafeSync Web Dashboard on port 8095...")
    app.run(host="0.0.0.0", port=8095, debug=False)
