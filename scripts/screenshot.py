"""Скриншоты дашборда (для проверки вида): запускает streamlit, снимает каждую вкладку.

Использование: python scripts/screenshot.py <out_dir> [lang]
"""
import subprocess
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "shots"
out.mkdir(parents=True, exist_ok=True)
PORT = 8601

proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", str(ROOT / "streamlit_app.py"), "--server.headless", "true",
     "--server.port", str(PORT), "--browser.gatherUsageStats", "false"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT,
)
try:
    for _ in range(60):
        try:
            if requests.get(f"http://localhost:{PORT}/_stcore/health", timeout=1).text == "ok":
                break
        except Exception:
            pass
        time.sleep(0.5)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": int(sys.argv[3]) if len(sys.argv) > 3 else 4200})
        page.goto(f"http://localhost:{PORT}", wait_until="networkidle")
        page.wait_for_timeout(4000)
        tabs = page.locator('[data-baseweb="tab-list"]').first.locator('[data-baseweb="tab"]')
        n = tabs.count()
        print("tabs:", n)
        for i in range(n):
            tabs.nth(i).click()
            page.wait_for_timeout(2500)
            page.screenshot(path=str(out / f"tab{i}.png"), full_page=True)
            print("saved", out / f"tab{i}.png")
        browser.close()
finally:
    proc.terminate()
    try:
        log = proc.communicate(timeout=5)[0]
    except Exception:
        proc.kill(); log = ""
    bad = [l for l in log.splitlines() if any(k in l for k in ("Error", "Traceback", "Warning", "warn"))]
    print("streamlit log issues:", bad if bad else "none")
