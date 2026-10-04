"""
theBeastFB CLI
  python main.py              # one full cycle
  python main.py --serve      # FastAPI :8000
  python main.py --scan-loop  # every 1500 s
"""
from __future__ import annotations
import argparse
import logging
import time
import uvicorn

from config.football_settings import SCAN_INTERVAL, MOCK_MODE, LOG_DIR
from core.football_beast import run_cycle
from core.football_derive import build_gold
from storage.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("beast.main")


def one_shot():
    init_db()
    build_gold()
    result = run_cycle(live_command=False)
    print("=== theBeastFB v2 ===")
    print(f"scan_id   : {result['scan_id']}")
    print(f"gold      : {result['gold']['rows']} rows")
    print(f"feed      : {result['feed_rows']} (soft={result['soft_rows']} pin={result['pinnacle_rows']})")
    print(f"mock      : {result['mock']}")
    print(f"credits   : {result['credits']}")
    for phase in ("prematch", "sim", "live"):
        print(f"\n-- {phase} ({len(result[phase])}) --")
        for p in result[phase]:
            print(
                f"  {p['event'][:28]:28} {p['market']:14} "
                f"@{p['odds']:5.2f} edge={p['edge']*100:5.1f}%  [{p['book']}]"
            )


def serve():
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False)


def scan_loop():
    init_db()
    build_gold()
    log.info("Scanner every %ss mock=%s", SCAN_INTERVAL, MOCK_MODE)
    while True:
        try:
            result = run_cycle(live_command=False)
            log.info(
                "cycle ok prematch=%d sim=%d live=%d feed=%d",
                len(result["prematch"]), len(result["sim"]),
                len(result["live"]), result["feed_rows"],
            )
            from services.telegram_bot import handle
            handle("/scan")
        except Exception as exc:
            log.exception("cycle failed: %s", exc)
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="theBeastFB full engine")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--scan-loop", action="store_true")
    args = parser.parse_args()
    if args.serve:
        serve()
    elif args.scan_loop:
        scan_loop()
    else:
        one_shot()
  
