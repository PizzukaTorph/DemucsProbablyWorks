#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from transcription import TranscriptionConfig, transcribe_melodic_stem


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a melodic audio stem to a draft MIDI file.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--instrument", choices=("bass", "guitar", "piano"), required=True)
    parser.add_argument("--subdivisions", type=int, default=4, help="Quantization subdivisions per beat")
    parser.add_argument("--min-note-ms", type=int, default=80)
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"input file does not exist: {args.input}")
    if args.subdivisions < 1:
        parser.error("--subdivisions must be at least 1")

    report = transcribe_melodic_stem(
        args.input,
        args.output,
        TranscriptionConfig(
            instrument=args.instrument,
            subdivisions_per_beat=args.subdivisions,
            min_note_ms=args.min_note_ms,
        ),
    )
    print(json.dumps({key: report[key] for key in ("output", "instrument", "bpm", "notes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
