"""Прогон приложения через streamlit.testing без браузера: все вкладки и языки."""
import sys
import time
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ok = True
for lang in ["ru", "kz", "en"]:
    t0 = time.time()
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=180)
    at.session_state["lang"] = lang
    at.run()
    errs = [e.value for e in at.exception]
    warns = [w.value for w in at.warning]
    print(f"[{lang}] {time.time()-t0:.1f}s  tabs={len(at.tabs)}  charts~={len([e for e in at.main])}  "
          f"exceptions={len(errs)}  warnings={len(warns)}")
    for e in errs:
        ok = False
        print("   EXC:", str(e)[:800])
    for w in warns:
        print("   WARN:", str(w)[:300])

print("SMOKE OK" if ok else "SMOKE FAILED")
sys.exit(0 if ok else 1)
