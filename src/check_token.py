"""CLI: แสดง Scopes ที่อยู่ใน token.json

Usage:
    python src/check_token.py
"""

import json

from ta_auth import TOKEN_FILE

with open(TOKEN_FILE) as f:
    token = json.load(f)

print("Scopes in token:")
scopes = token.get("scopes", [])
if isinstance(scopes, list):
    for s in scopes:
        print(" -", s)
else:
    for s in scopes.split():
        print(" -", s)