from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib import error, request

SCRIPTS_ROOT = Path(__file__).resolve().parent

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from generate_demo_data import (  # noqa: E402
    build_large_demo_records,
    build_payload,
    load_quick_demo_records,
    load_source_rows,
)


def fetch_json(url: str, timeout_seconds: float) -> dict | list:
    with request.urlopen(url, timeout=timeout_seconds) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def post_batch(api_base_url: str, records: list[dict[str, object]], timeout_seconds: float) -> dict:
    payload = json.dumps({"records": records}).encode("utf-8")
    http_request = request.Request(
        f"{api_base_url}/sensor-readings/batch",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def chunk_records(records: list[dict[str, object]], batch_size: int) -> list[list[dict[str, object]]]:
    return [records[index : index + batch_size] for index in range(0, len(records), batch_size)]


def build_records(mode: str, records_per_machine: int) -> list[dict[str, object]]:
    rows_by_udi, _, _ = load_source_rows()
    if mode == "quick":
        seeds = load_quick_demo_records()
    else:
        seeds = build_large_demo_records(records_per_machine)

    return [
        build_payload(seed, rows_by_udi[int(seed["source_udi"])])
        for seed in seeds
    ]


def print_summary(summary: dict[str, object]) -> None:
    print(
        "Batch accepted:",
        f"processed={summary['processed_records']},",
        f"predictions={summary['created_predictions']},",
        f"alerts={summary['created_alerts']}",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate incoming machine sensor data by posting deterministic batches "
            "to the live FastAPI backend."
        )
    )
    parser.add_argument(
        "--api-base-url",
        default="http://localhost:8000",
        help="Base URL for the running FastAPI backend.",
    )
    parser.add_argument(
        "--mode",
        choices=["quick", "stream"],
        default="quick",
        help="Quick sends a small deterministic batch. Stream sends multiple deterministic batches.",
    )
    parser.add_argument(
        "--records-per-machine",
        type=int,
        default=12,
        help="Only used in stream mode. Number of generated readings per machine.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=6,
        help="Number of records to send per POST request.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=1.0,
        help="Pause between posted batches in stream mode.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="HTTP timeout for health checks and batch POSTs.",
    )
    args = parser.parse_args()

    api_base_url = args.api_base_url.rstrip("/")

    try:
        health = fetch_json(f"{api_base_url}/health", timeout_seconds=args.timeout_seconds)
    except error.URLError as exc:
        raise SystemExit(
            f"Unable to reach backend health endpoint at {api_base_url}/health: {exc}"
        ) from exc

    print("Backend health:")
    print(json.dumps(health, indent=2))

    try:
        records = build_records(
            mode=args.mode,
            records_per_machine=args.records_per_machine,
        )
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    batches = chunk_records(records, batch_size=max(1, args.batch_size))

    total_predictions = 0
    total_alerts = 0

    for index, batch in enumerate(batches, start=1):
        try:
            summary = post_batch(
                api_base_url=api_base_url,
                records=batch,
                timeout_seconds=args.timeout_seconds,
            )
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(
                f"Batch {index} failed with HTTP {exc.code}: {detail}"
            ) from exc
        except error.URLError as exc:
            raise SystemExit(f"Batch {index} failed to reach the backend: {exc}") from exc

        total_predictions += int(summary["created_predictions"])
        total_alerts += int(summary["created_alerts"])

        print(f"Posted batch {index}/{len(batches)} with {len(batch)} records.")
        print_summary(summary)

        if args.mode == "stream" and index < len(batches):
            time.sleep(max(0.0, args.interval_seconds))

    predictions = fetch_json(
        f"{api_base_url}/predictions?limit=500",
        timeout_seconds=args.timeout_seconds,
    )
    alerts = fetch_json(
        f"{api_base_url}/alerts?limit=500",
        timeout_seconds=args.timeout_seconds,
    )

    print("Simulation complete.")
    print(f"Records posted: {len(records)}")
    print(f"Predictions created this run: {total_predictions}")
    print(f"Alerts created this run: {total_alerts}")
    print(f"Current stored predictions returned by API: {len(predictions)}")
    print(f"Current stored alerts returned by API: {len(alerts)}")


if __name__ == "__main__":
    main()
