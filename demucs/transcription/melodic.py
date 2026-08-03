from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import librosa
import mido
import numpy as np


@dataclass(frozen=True)
class TranscriptionConfig:
    instrument: str = "guitar"
    sample_rate: int = 22050
    hop_length: int = 512
    subdivisions_per_beat: int = 4
    min_note_ms: int = 80


RANGES = {
    "bass": ("E1", "C5"),
    "guitar": ("E2", "E6"),
    "piano": ("A0", "C8"),
}


def _quantize(seconds: float, bpm: float, subdivisions: int) -> float:
    step = 60.0 / bpm / subdivisions
    return round(seconds / step) * step


def _segments(notes: np.ndarray, times: np.ndarray, min_seconds: float):
    start = 0
    current = notes[0] if len(notes) else np.nan
    for index in range(1, len(notes) + 1):
        changed = index == len(notes) or notes[index] != current
        if not changed:
            continue
        if not np.isnan(current):
            end_time = times[min(index, len(times) - 1)]
            start_time = times[start]
            if end_time - start_time >= min_seconds:
                yield int(current), float(start_time), float(end_time)
        if index < len(notes):
            start = index
            current = notes[index]


def transcribe_melodic_stem(input_path: str | Path, output_path: str | Path, config: TranscriptionConfig) -> dict:
    source = Path(input_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    y, sr = librosa.load(source, sr=config.sample_rate, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr, hop_length=config.hop_length)
    bpm = float(np.asarray(tempo).reshape(-1)[0])
    low, high = RANGES[config.instrument]
    f0, voiced, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz(low),
        fmax=librosa.note_to_hz(high),
        sr=sr,
        hop_length=config.hop_length,
    )
    midi_notes = np.where(voiced & ~np.isnan(f0), np.rint(librosa.hz_to_midi(f0)), np.nan)
    times = librosa.times_like(f0, sr=sr, hop_length=config.hop_length)

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name=f"{config.instrument} transcription", time=0))
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))

    last_tick = 0
    events = []
    for note, raw_start, raw_end in _segments(midi_notes, times, config.min_note_ms / 1000):
        start = max(0.0, _quantize(raw_start, bpm, config.subdivisions_per_beat))
        end = max(start + 0.01, _quantize(raw_end, bpm, config.subdivisions_per_beat))
        start_tick = round(mido.second2tick(start, mid.ticks_per_beat, mido.bpm2tempo(bpm)))
        end_tick = round(mido.second2tick(end, mid.ticks_per_beat, mido.bpm2tempo(bpm)))
        track.append(mido.Message("note_on", note=note, velocity=80, time=max(0, start_tick - last_tick)))
        track.append(mido.Message("note_off", note=note, velocity=0, time=max(1, end_tick - start_tick)))
        last_tick = end_tick
        events.append({"note": note, "start": start, "end": end})

    mid.save(target)
    report = {"input": str(source), "output": str(target), "instrument": config.instrument, "bpm": bpm, "notes": len(events), "events": events}
    target.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
