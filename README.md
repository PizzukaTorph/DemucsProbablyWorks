# DemucsProbablyWorks

A lightweight, questionably-engineered wrapper around Demucs. Built for people who “just want to split a track” without reading 40 pages of academic papers or compiling PyTorch at 3 AM.

## Why this exists

Because Demucs is amazing, but:

- sometimes you just want to throw a file at it and hope for the best
- you don’t want to memorize the CLI every time
- you don’t want to pretend you understand complicated model names
- and mostly because no one had made a tool that openly admits it probably works

## What it does

- Accepts an audio file
- Sends it to Demucs for separation
- Crosses fingers
- Returns stems (vocals, bass, drums, etc.)
- Generates draft MIDI and JSON note reports for bass, guitar, and piano stems

## Requirements

- Python for the Demucs worker
- Docker and Docker Compose
- A bit of patience, especially on CPU

## Installation

```bash
git clone <repo-url>
cd DemucsProbablyWorks
docker compose build
docker compose up -d
```

Open the web UI at `http://localhost:3000`.

## Output

After separation and transcription:

```text
output/htdemucs_6s/<track>/
  drums.wav
  bass.wav
  bass.mid
  bass.json
  guitar.wav
  guitar.mid
  guitar.json
  piano.wav
  piano.mid
  piano.json
  vocals.wav
  other.wav
```

## MIDI presets

Automatic transcription uses the `clean` preset by default. It applies pitch-confidence filtering, median smoothing, minimum-note filtering, semitone tolerance, nearby-note merging, and final quantization.

```yaml
demucs:
  environment:
    MIDI_PRESET: clean
```

Available presets:

- `clean`: aggressive cleanup for tablature and manual editing
- `draft`: preserves more detail but produces noisier MIDI

Manual usage:

```bash
python /app/transcribe.py \
  /app/output/htdemucs_6s/song/bass.wav \
  /app/output/htdemucs_6s/song/bass.mid \
  --instrument bass \
  --preset clean
```

The current transcription engine is monophonic. Bass generally produces the best results. Chord-heavy or distorted guitar and piano stems still require manual correction; a polyphonic backend is planned separately rather than forcing a large TensorFlow dependency into the default worker image.

## Files and directories

- `backend/` — Node.js backend and web UI
- `demucs/` — Demucs worker and MIDI transcription code
- `uploads/` — incoming files
- `output/` — generated stems, MIDI files, reports, and status JSON

The worker ignores hidden files such as `.gitkeep` and only processes supported audio extensions.

## Tests

```bash
cd demucs
python -m unittest discover -s tests
```

## License

MIT
