#!/usr/bin/env python3
"""Print bounded, recoverable diagnostic slices from Unreal Engine logs."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ERROR_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"fatal error",
        r"\berror\s+LNK\d+\b",
        r"\berror\s+C\d+\b",
        r":\s*error(?:\s|:)",
        r"Log[^:]*:\s*Error:",
        r"UnrealBuildTool.*ERROR",
        r"AutomationTool exiting with ExitCode=[1-9]",
        r"BUILD FAILED",
        r"Assertion failed:",
        r"ensure condition failed",
        r"Unhandled Exception",
        r"EXCEPTION_ACCESS_VIOLATION",
    )
]
WARNING_PATTERN = re.compile(r"\bwarning\b|Log[^:]*:\s*Warning:", re.IGNORECASE)


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--before", type=int, default=3)
    parser.add_argument("--after", type=int, default=10)
    parser.add_argument("--max-groups", type=int, default=20)
    parser.add_argument("--tail", type=int, default=80)
    args = parser.parse_args()

    path = args.log.resolve()
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    matches = [
        index
        for index, line in enumerate(lines)
        if any(pattern.search(line) for pattern in ERROR_PATTERNS)
    ]
    warnings = sum(1 for line in lines if WARNING_PATTERN.search(line))
    digest = hashlib.sha256(raw).hexdigest()

    print(f"LOG: {path}")
    print(f"SHA256: {digest}")
    print(f"LINES: {len(lines)}  ERROR_MATCHES: {len(matches)}  WARNING_LINES: {warnings}")

    if matches:
        ranges = [
            (max(0, index - args.before), min(len(lines) - 1, index + args.after))
            for index in matches
        ]
        all_ranges = merge_ranges(ranges)
        selected = all_ranges[: args.max_groups]
        print(f"GROUPS_SHOWN: {len(selected)}")
        for group_index, (start, end) in enumerate(selected, 1):
            print(f"\n--- ERROR GROUP {group_index}: lines {start + 1}-{end + 1} ---")
            for line_index in range(start, end + 1):
                print(f"{line_index + 1:>7}: {lines[line_index]}")
        if len(all_ranges) > len(selected):
            print("\nMORE_ERROR_GROUPS_EXIST: rerun with --max-groups or inspect the original log.")
    else:
        start = max(0, len(lines) - args.tail)
        print(f"NO_ERROR_PATTERN_MATCHED; showing final {len(lines) - start} lines.")
        for line_index in range(start, len(lines)):
            print(f"{line_index + 1:>7}: {lines[line_index]}")

    print(f"\nFULL_LOG_REMAINS_AT: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
