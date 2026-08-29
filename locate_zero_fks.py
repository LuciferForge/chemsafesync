#!/usr/bin/env python3
"""
Locate Zero_fks directory and .env file paths
"""

import os
from pathlib import Path
from dotenv import load_dotenv

candidate_paths = [
    Path("/Users/apple/Documents/Zero_fks/.env"),
    Path("/Users/apple/Documents/Zero_fks/Zero_fks/.env"),
    Path("/Users/apple/Zero_fks/.env"),
    Path("/Users/apple/Documents/LuciferForge/Zero_fks/.env"),
    Path("/Users/apple/Documents/products/Zero_fks/.env")
]

print("================================================")
print("      🔍 CHECKING ZERO_FKS .ENV PATHS           ")
print("================================================")
found_env = None
for p in candidate_paths:
    print(f"Checking: {p} -> Exists: {'YES' if p.exists() else 'NO'}")
    if p.exists():
        found_env = p
        load_dotenv(p)

if found_env:
    print(f"\n✅ LOADED .ENV FROM: {found_env}")
    r_key = os.getenv("RESEND_API_KEY")
    g_pass = os.getenv("GMAIL_APP_PASSWORD")
    g_email = os.getenv("GMAIL_FROM_EMAIL")
    print(f"• RESEND_API_KEY:    {'PRESENT (Length: ' + str(len(r_key)) + ')' if r_key else 'NOT FOUND'}")
    print(f"• GMAIL_APP_PASSWORD: {'PRESENT (Length: ' + str(len(g_pass)) + ')' if g_pass else 'NOT FOUND'}")
    print(f"• GMAIL_FROM_EMAIL:   {g_email if g_email else 'NOT FOUND'}")
print("================================================")
