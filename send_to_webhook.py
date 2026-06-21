#!/usr/bin/env python3
"""Send recent call history CSV to webhook for Google Calendar sync."""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Send call history to webhook")
    parser.add_argument("--csv", default="calls.csv", help="Path to calls CSV (default: calls.csv)")
    parser.add_argument(
        "--weeks",
        type=int,
        default=None,
        help="Only send calls from the last N weeks (default: all)",
    )
    parser.add_argument("--webhook-url", help="Webhook URL (or set WEBHOOK_URL env var)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be sent without sending",
    )
    args = parser.parse_args()

    webhook_url = args.webhook_url or os.environ.get("WEBHOOK_URL", "")
    if not webhook_url and not args.dry_run:
        print("Error: --webhook-url or WEBHOOK_URL env var required", file=sys.stderr)
        sys.exit(1)

    cutoff = datetime.now().astimezone() - timedelta(weeks=args.weeks) if args.weeks else None

    calls = []
    with open(args.csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("answered", "").lower() not in ("true", "1"):
                continue
            if not row.get("unique_id"):
                continue
            start = row.get("start", "")
            if not start:
                continue
            if cutoff:
                try:
                    call_dt = datetime.fromisoformat(start)
                    if call_dt < cutoff:
                        continue
                except ValueError:
                    continue
            calls.append(row)

    if not calls:
        print("No matching calls found.", file=sys.stderr)
        sys.exit(1)

    period = f"the last {args.weeks} week(s)" if args.weeks else "all time"
    print(f"Found {len(calls)} answered calls ({period})")

    if args.dry_run:
        for c in calls[:10]:
            name = c.get("contact_name") or c.get("phone_number") or "Unknown"
            print(f"  {c['direction']:>8} | {name} | {c['start'][:16]} | {c['duration']}")
        if len(calls) > 10:
            print(f"  ... and {len(calls) - 10} more")
        return

    if not webhook_url.lower().startswith("https://"):
        print("Error: webhook URL must use HTTPS", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps({"calls": calls}).encode()
    req = Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=10) as resp:
            print(f"Response: {resp.status} {resp.reason}")
            body = resp.read().decode()
            if body:
                print(body)
    except Exception as e:
        print(f"Webhook request failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
