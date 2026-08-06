from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import json

import librosa
import mido
import numpy as np


@dataclass(frozen=True)
class TranscriptionConfig:
    instrument: str = "guitar"
    preset: str = "clean"
    sample_rate: int = 22050
    hop_length: int = 512
    subdivisions_per_beat: int = 4
    min_note_ms: int = 140
    merge_gap_ms: int = 90
    pitch_tolerance: int = 1
    voiced_probability: float = 0.75
    median_window: int = 9


RANGES = {
    "bass": ("E1", "G4"),
    "guitar": ("E2", "E6"),
    "piano": ("A0", "C8"),
}

PRESETS = {
    "draft": {
        "min_note_ms": 70,
        "merge_gap_ms": 45,
        "pitch_tolerance": 0,
        "voiced_probability": 0.55,
        "median_window": 5,
    },
    "clean": {
        "min_note_ms": 140,
        "merge_gap_ms": 90,
        "pitch_tolerance": 1,
        "voiced_probability": 0.75,
        "median_window": 9,
    },
}


def apply_preset(config: TranscriptionConfig) -> TranscriptionConfig:
    values = PRESETS.get(config.preset)
    if values is None:
        raise ValueError(f"unknown transcription preset: {config.preset}")
    return replace(config, **values)


def _quantize(seconds: float, bpm: float, subdivisions: int) -> float:
    step = 60.0 / bpm / subdivisions
    return round(seconds / step) * step


def _median_smooth(values: np.ndarray, window: int) -> np.ndarray:
    if window <= 1 or len(values) == 0:
        return values.copy()
    if window % 2 == 0:
        window += 1
    result = values.copy()
    half = window // 2
    for index in range(len(values)):
        start = max(0, index - half)
        end = min(len(values), index + half + 1)
        chunk = values[start:end]
        finite = chunk[np.isfinite(chunk)]
        result[index] = np.median(finite) if len(finite) else np.nan
    return result


def _raw_segments(notes: np.ndarray, times: np.ndarray):
    start = None
    values: list[float] = []
    for index, note in enumerate(notes):
        if np.isfinite(note):
            if start is None:
                start = index
            values.append(float(note))
            continue
        if start is not None:
            yield start, index, values
            start = None
            values = []
    if start is not None:
        yield start, len(notes), values


def _split_pitch_changes(start: int, end: int, notes: np.ndarray, tolerance: int):
    segment_start = start
    anchor = float(notes[start])
    for index in range(start + 1, end):
        value = float(notes[index])
        if abs(value - anchor) <= tolerance:
            anchor = (anchor * 0.8) + (value * 0.2)
            continue
        yield segment_start, index
        segment_start = index
        anchor = value
    yield segment_start, end


def _build_events(notes: np.ndarray, times: np.ndarray, config: TranscriptionConfig):
    events = []
    min_seconds = config.min_note_ms / 1000.0
    for raw_start, raw_end, _ in _raw_segments(notes, times):
        for start_index, end_index in _split_pitch_changes(
            raw_start, raw_end, notes, config.pitch_tolerance
        ):
            start = float(times[start_index])
            end = float(times[min(end_index, len(times) - 1)])
            if end - start < min_seconds:
                continue
            pitch_values = notes[start_index:end_index]
            finite = pitch_values[np.isfinite(pitch_values)]
            if not len(finite):
                continue
            events.append(
                {
                    "note": int(round(float(np.median(finite)))),
                    "start": start,
                    "end": end,
                }
            )
    return events


def _merge_events(events: list[dict], config: TranscriptionConfig) -> list[dict]:
    if not events:
        return []
    merged = [events[0].copy()]
    max_gap = config.merge_gap_ms / 1000.0
    for event in events[1:]:
        previous = merged[-1]
        gap = event["start"] - previous["end"]
        same_pitch = abs(event["note"] - previous["note"]) <= config.pitch_tolerance
        if same_pitch and gap <= max_gap:
            previous["end"] = max(previous["end"], event["end"])
            previous["note"] = int(round((previous["note"] + event["note"]) / 2))
        else:
            merged.append(event.copy())
    return merged


def _quantize_events(events: list[dict], bpm: float, subdivisions: int) -> list[dict]:
    quantized = []
    for event in events:
        start = max(0.0, _quantize(event["start"], bpm, subdivisions))
        end = max(start + 0.01, _quantize(event["end"], bpm, subdivisions))
        if quantized and start < quantized[-1]["end"]:
            start = quantized[-1]["end"]
        if end <= start:
            continue
        quantized.append({"note": event["note"], "start": start, "end": end})
    return quantized


def transcribe_melodic_stem(
    input_path: str | Path,
    output_path: str | Path,
    config: TranscriptionConfig,
) -> dict:
    config = apply_preset(config)
    source = Path(input_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    y, sr = librosa.load(source, sr=config.sample_rate, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr, hop_length=config.hop_length)
    bpm = float(np.asarray(tempo).reshape(-1)[0])
    if not np.isfinite(bpm) or bpm <= 0:
        bpm = 120.0

    low, high = RANGES[config.instrument]
    f0, voiced, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz(low),
        fmax=librosa.note_to_hz(high),
        sr=sr,
        hop_length=config.hop_length,
    )
    reliable = voiced & ~np.isnan(f0) & (voiced_prob >= config.voiced_probability)
    raw_midi = np.where(reliable, librosa.hz_to_midi(f0), np.nan)
    smoothed = _median_smooth(raw_midi, config.median_window)
    times = librosa.times_like(f0, sr=sr, hop_length=config.hop_length)

    events = _build_events(smoothed, times, config)
    events = _merge_events(events, config)
    events = _quantize_events(events, bpm, config.subdivisions_per_beat)

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name=f"{config.instrument} transcription", time=0))
    tempo_value = mido.bpm2tempo(bpm)
    track.append(mido.MetaMessage("set_tempo", tempo=tempo_value, time=0))

    last_tick = 0
    for event in events:
        start_tick = round(mido.second2tick(event["start"], mid.ticks_per_beat, tempo_value))
        end_tick = round(mido.second2tick(event["end"], mid.ticks_per_beat, tempo_value))
        track.append(
            mido.Message(
                "note_on",
                note=event["note"],
                velocity=80,
                time=max(0, start_tick - last_tick),
            )
        )
        track.append(
            mido.Message(
                "note_off",
                note=event["note"],
                velocity=0,
                time=max(1, end_tick - start_tick),
            )
        )
        last_tick = end_tick

    mid.save(target)
    report = {
        "input": str(source),
        "output": str(target),
        "instrument": config.instrument,
        "preset": config.preset,
        "bpm": bpm,
        "notes": len(events),
        "config": {
            "minNoteMs": config.min_note_ms,
            "mergeGapMs": config.merge_gap_ms,
            "pitchTolerance": config.pitch_tolerance,
            "voicedProbability": config.voiced_probability,
            "medianWindow": config.median_window,
            "subdivisionsPerBeat": config.subdivisions_per_beat,
        },
        "events": events,
    }
    target.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
