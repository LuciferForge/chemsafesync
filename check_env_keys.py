#!/usr/bin/env python3
"""
Inspect loaded environment variable names (without printing secret values) to locate Resend / Gmail API keys.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load all known .env files
dotenv_paths = [
    Path("/Users/apple/Documents/ZeroLag/.env"),
    Path("/Users/apple/Documents/products/polymarket-api/.env"),
    Path("/Users/apple/Documents/products/news-orderbook-arbitrage/.env"),
    Path("/Users/apple/Documents/LuciferForge/.env"),
    Path("/Users/apple/.env")
]

for p in dotenv_paths:
    if p.exists():
        load_dotenv(p)

keys = list(os.environ.keys())
matching_keys = [k for k in keys if any(term in k.upper() for term in ["RESEND", "GMAIL", "SMTP", "EMAIL", "MAIL", "SENDGRID"])]

print("================================================")
print("      🔑 DETECTED EMAIL & DISPATCH KEYS         ")
print("================================================")
print(f"Total env keys loaded: {len(keys)}")
print(f"Matching Email Keys Found: {matching_keys}")
for mk in matching_keys:
    val = os.getenv(mk, '')
    print(f"• Key: {mk} | Present: {'YES' if val else 'NO'} | Length: {len(val)}")
print("================================================")
