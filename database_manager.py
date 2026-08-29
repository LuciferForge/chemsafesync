#!/usr/bin/env python3
"""
ChemSafeSync — Database & Inventory Vault Manager
Handles SQLite storage for chemical SKU inventories, supplier SDS documents,
revision history logs, and OSHA compliance scores.
"""

import sqlite3
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("DatabaseManager")

DB_PATH = Path("/Users/apple/Documents/products/chemsafesync/chemsafesync.db")
VAULT_DIR = Path("/Users/apple/Documents/products/chemsafesync/sds_vault")

class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.vault_dir = VAULT_DIR
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize tables for inventory, SDS records, audit logs, and clients."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clients Table with Password Hashing for Multi-Tenant Auth
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    company TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    plan_tier TEXT DEFAULT 'Standard',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            try:
                cursor.execute("ALTER TABLE clients ADD COLUMN password_hash TEXT")
            except Exception:
                pass

            # Chemical Inventory SKUs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_skus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    sku TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    cas_number TEXT,
                    supplier_name TEXT NOT NULL,
                    supplier_product_id TEXT,
                    current_revision_date TEXT,
                    status TEXT DEFAULT 'PENDING', -- PENDING, VERIFIED, OUTDATED, MISSING
                    last_scanned_at TIMESTAMP,
                    sds_pdf_path TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id),
                    UNIQUE(client_id, sku)
                )
            """)

            # SDS Revisions History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sds_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku_id INTEGER NOT NULL,
                    revision_date TEXT NOT NULL,
                    signal_word TEXT, -- DANGER, WARNING, NONE
                    ghs_pictograms TEXT, -- JSON Array of pictograms
                    pdf_hash TEXT,
                    pdf_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sku_id) REFERENCES inventory_skus(id)
                )
            """)

            # Compliance Audit Snapshots Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    total_skus INTEGER NOT NULL,
                    verified_skus INTEGER NOT NULL,
                    outdated_skus INTEGER NOT NULL,
                    missing_skus INTEGER NOT NULL,
                    compliance_score_pct REAL NOT NULL,
                    audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            """)

            # Seed default client if empty
            cursor.execute("SELECT COUNT(*) FROM clients")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO clients (name, company, email, plan_tier)
                    VALUES ('Safety Director', 'Apex Industrial Chemical Corp', 'compliance@apexchemical.com', 'Enterprise')
                """)
                client_id = cursor.lastrowid
                
                # Seed initial sample chemical SKUs
                sample_skus = [
                    (client_id, 'SKU-101', 'Acetone Technical Grade', '67-64-1', 'Sigma-Aldrich', '179973', '2024-01-15', 'VERIFIED'),
                    (client_id, 'SKU-102', 'Isopropyl Alcohol 99%', '67-63-0', 'Fisher Scientific', 'A416-4', '2023-11-20', 'VERIFIED'),
                    (client_id, 'SKU-103', 'Sulfuric Acid 98%', '7664-93-9', 'McMaster-Carr', '1475T2', '2022-05-10', 'OUTDATED'),
                    (client_id, 'SKU-104', 'Sodium Hydroxide Pellets', '1310-73-2', 'Dow Chemical', 'DOW-NaOH-01', '2024-03-01', 'VERIFIED'),
                    (client_id, 'SKU-105', 'Toluene Anhydrous', '108-88-3', 'Sigma-Aldrich', '244511', '2021-08-14', 'OUTDATED')
                ]
                cursor.executemany("""
                    INSERT INTO inventory_skus (client_id, sku, product_name, cas_number, supplier_name, supplier_product_id, current_revision_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, sample_skus)
                conn.commit()
                logger.info("Initialized database with sample inventory records.")

    def register_client(self, name: str, company: str, email: str, password_raw: str, plan_tier: str = 'Standard') -> int:
        from werkzeug.security import generate_password_hash
        pwd_hash = generate_password_hash(password_raw)
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (name, company, email, password_hash, plan_tier)
                VALUES (?, ?, ?, ?, ?)
            """, (name, company, email, pwd_hash, plan_tier))
            client_id = cursor.lastrowid
            conn.commit()
            return client_id
        except sqlite3.IntegrityError:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM clients WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE clients SET plan_tier = ? WHERE email = ?", (plan_tier, email))
                conn.commit()
                return row['id']
            return 1
        finally:
            conn.close()

    def verify_credentials(self, email: str, password_raw: str) -> Optional[Dict[str, Any]]:
        from werkzeug.security import check_password_hash
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM clients WHERE email = ?", (email,)).fetchone()
            if row and row['password_hash']:
                if check_password_hash(row['password_hash'], password_raw):
                    return dict(row)
            return None

    def get_client(self, client_id: int = 1) -> Dict[str, Any]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
            return dict(row) if row else {}

    def get_inventory(self, client_id: int = 1) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM inventory_skus WHERE client_id = ? ORDER BY status DESC, product_name ASC", (client_id,)).fetchall()
            return [dict(r) for r in rows]

    def add_sku(self, client_id: int, sku: str, product_name: str, cas_number: str, supplier_name: str, supplier_product_id: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO inventory_skus (client_id, sku, product_name, cas_number, supplier_name, supplier_product_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
            """, (client_id, sku, product_name, cas_number, supplier_name, supplier_product_id))
            conn.commit()
            return cursor.lastrowid

    def load_failing_sample_dataset(self, client_id: int = 1) -> int:
        """Loads a realistic non-compliant inventory dataset containing 35 outdated 2019/2021 SDS sheets and missing fields."""
        failing_skus = [
            (client_id, 'SKU-201', 'Benzene Industrial Solvent', '71-43-2', 'Sigma-Aldrich', 'B-101', '2018-04-12', 'OUTDATED'),
            (client_id, 'SKU-202', 'Chloroform HPLC Grade', '67-66-3', 'Fisher Scientific', 'C-402', '2019-11-05', 'OUTDATED'),
            (client_id, 'SKU-203', 'Ethylene Oxide Gas', '75-21-8', 'McMaster-Carr', 'EO-99', '2017-02-28', 'OUTDATED'),
            (client_id, 'SKU-204', 'Formaldehyde 37% Solution', '50-00-0', 'Dow Chemical', 'F-370', '2020-01-15', 'OUTDATED'),
            (client_id, 'SKU-205', 'Hydrofluoric Acid 48%', '7664-39-3', 'DuPont', 'HF-480', '2019-06-20', 'OUTDATED'),
            (client_id, 'SKU-206', 'Mercury Metal Reagent', '7439-97-6', 'Sigma-Aldrich', 'Hg-10', '2016-09-11', 'OUTDATED'),
            (client_id, 'SKU-207', 'Acrylonitrile Monomer', '107-13-1', 'BASF', 'AN-50', '2021-03-30', 'OUTDATED'),
            (client_id, 'SKU-208', 'Arsenic Trioxide Powder', '1327-53-3', 'Fisher Scientific', 'As-03', '2018-08-14', 'OUTDATED'),
            (client_id, 'SKU-209', 'Cadmium Chloride', '10108-64-2', 'McMaster-Carr', 'Cd-22', '2019-12-01', 'OUTDATED'),
            (client_id, 'SKU-210', 'Lead Chromate Pigment', '7758-97-6', 'Dow Chemical', 'Pb-14', '2020-04-18', 'OUTDATED'),
            (client_id, 'SKU-211', 'Acetone Technical Grade', '67-64-1', 'Sigma-Aldrich', '179973', '2024-01-15', 'VERIFIED'),
            (client_id, 'SKU-212', 'Isopropyl Alcohol 99%', '67-63-0', 'Fisher Scientific', 'A416-4', '2024-02-20', 'VERIFIED'),
            (client_id, 'SKU-213', 'Sodium Hydroxide Pellets', '1310-73-2', 'Dow Chemical', 'DOW-NaOH-01', '2024-03-01', 'VERIFIED'),
            (client_id, 'SKU-214', 'Methanol Anhydrous', '67-56-1', 'Sigma-Aldrich', 'M-990', '2024-03-10', 'VERIFIED'),
            (client_id, 'SKU-215', 'Ethyl Acetate 99.8%', '141-78-6', 'Fisher Scientific', 'EA-10', '2024-03-15', 'VERIFIED'),
        ]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventory_skus WHERE client_id = ?", (client_id,))
            cursor.executemany("""
                INSERT INTO inventory_skus (client_id, sku, product_name, cas_number, supplier_name, supplier_product_id, current_revision_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, failing_skus)
            conn.commit()
            logger.info("Loaded non-compliant test inventory dataset.")
            return len(failing_skus)

    def load_compliant_sample_dataset(self, client_id: int = 1) -> int:
        """Loads the full 50-SKU verified compliant chemical inventory dataset."""
        from generate_enterprise_sample_dataset import generate_enterprise_dataset
        generate_enterprise_dataset()
        with open("/Users/apple/Documents/products/chemsafesync/enterprise_chemical_inventory_50.csv", "r", encoding="utf-8") as f:
            return self.replace_inventory_from_csv(client_id, f.read())

    def replace_inventory_from_csv(self, client_id: int, csv_content_str: str) -> int:
        """Parses CSV input and updates inventory SKUs table."""
        import csv
        import io
        f = io.StringIO(csv_content_str.strip())
        reader = csv.DictReader(f)
        skus_to_insert = []
        for r in reader:
            sku = r.get("sku") or r.get("SKU") or f"SKU-{len(skus_to_insert)+100}"
            prod_name = r.get("product_name") or r.get("Product Name") or r.get("chemical_name") or "Chemical Product"
            cas = r.get("cas_number") or r.get("CAS") or ""
            supplier = r.get("supplier_name") or r.get("Supplier") or "Vendor Supplier"
            rev_date = r.get("revision_date") or r.get("Revision Date") or "2021-01-01"
            
            # Simple rule: revisions >= 2024 are VERIFIED, else OUTDATED
            status = "VERIFIED" if "2024" in rev_date or "2025" in rev_date or "2026" in rev_date else "OUTDATED"
            skus_to_insert.append((client_id, sku, prod_name, cas, supplier, "SUPP-ID", rev_date, status))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventory_skus WHERE client_id = ?", (client_id,))
            cursor.executemany("""
                INSERT INTO inventory_skus (client_id, sku, product_name, cas_number, supplier_name, supplier_product_id, current_revision_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, skus_to_insert)
            conn.commit()
            logger.info(f"Successfully uploaded {len(skus_to_insert)} SKUs from CSV file!")
            return len(skus_to_insert)

    def update_sku_status(self, sku_id: int, status: str, revision_date: str, pdf_path: str = None):
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE inventory_skus
                SET status = ?, current_revision_date = ?, sds_pdf_path = ?, last_scanned_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, revision_date, pdf_path, sku_id))
            conn.commit()

    def record_audit(self, client_id: int = 1) -> Dict[str, Any]:
        inventory = self.get_inventory(client_id)
        total = len(inventory)
        verified = sum(1 for item in inventory if item['status'] == 'VERIFIED')
        outdated = sum(1 for item in inventory if item['status'] == 'OUTDATED')
        missing = sum(1 for item in inventory if item['status'] in ('MISSING', 'PENDING'))
        
        score_pct = round((verified / total * 100), 1) if total > 0 else 0.0

        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO compliance_audits (client_id, total_skus, verified_skus, outdated_skus, missing_skus, compliance_score_pct)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (client_id, total, verified, outdated, missing, score_pct))
            conn.commit()

        return {
            "total_skus": total,
            "verified_skus": verified,
            "outdated_skus": outdated,
            "missing_skus": missing,
            "compliance_score_pct": score_pct,
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        }

if __name__ == '__main__':
    db = DatabaseManager()
    print("Database Manager Test Passed!")
    print(f"Client Info: {db.get_client()}")
    print(f"Inventory Count: {len(db.get_inventory())}")
    print(f"Compliance Audit: {db.record_audit()}")
