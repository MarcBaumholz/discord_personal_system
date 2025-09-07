#!/usr/bin/env python3
"""Health check: verifies that each bot log has been updated recently (last 5 minutes)."""
import os, time, sys
from pathlib import Path

BOT_NAMES = ["money", "calories", "allgemeine", "preisvergleich", "erinnerungen"]
LOG_DIR = Path("logs/multibot")
now = time.time()
missing = []
for name in BOT_NAMES:
    lp = LOG_DIR / f"{name}.log"
    if not lp.exists():
        missing.append(name)
        continue
    if now - lp.stat().st_mtime > 300:  # 5 minutes
        missing.append(name)

if missing:
    print(f"Unhealthy: stale or missing logs for: {', '.join(missing)}")
    sys.exit(1)
print("Healthy")
