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
- Automatically generates draft MIDI files for `bass.wav`, `guitar.wav`, and `piano.wav`

MIDI transcription is enabled by default. Set `AUTO_TRANSCRIBE=false` on the Demucs worker to disable it.

## What it does NOT do
- Improve Demucs
- Be faster than Demucs
- Be smarter than Demucs
- Replace Demucs
- Promise production-ready tablature from distorted or polyphonic audio

If the output sounds odd, that’s likely Demucs — not this wrapper.

## Requirements
- Python (for the Demucs worker)
- Docker & docker-compose (recommended for easy setup)
- A bit of patience (Demucs can be slow on CPU)

## Installation (quick)
Clone the repo, then use docker-compose:

```bash
git clone <repo-url>
cd project-demucs
docker-compose build
docker-compose up -d
```

After pulling transcription changes, rebuild the worker image so the new Python dependencies and scripts are installed:

```bash
docker compose build demucs
docker compose up -d demucs
```

Note: building the Demucs image can take time and requires network access to download Python packages and models.

## Usage
Open the web UI at: http://localhost:3000

Upload a file and choose a model. The backend saves the file to `./uploads`; the Demucs worker separates it into `./output` and then transcribes supported melodic stems.

For a song named `song.wav`, expected output includes:

```text
output/htdemucs_6s/song/
├── bass.wav
├── bass.mid
├── bass.json
├── drums.wav
├── guitar.wav
├── guitar.mid
├── guitar.json
├── piano.wav
├── piano.mid
├── piano.json
├── vocals.wav
└── other.wav
```

Only stems produced by the selected Demucs model can be transcribed. The default `htdemucs_6s` model produces separate guitar and piano stems.

### Manual transcription

```bash
python /app/transcribe.py \
  /app/output/htdemucs_6s/song/bass.wav \
  /app/output/htdemucs_6s/song/bass.mid \
  --instrument bass
```

### Status & progress
The worker writes per-file status JSON into `output/status/<filename>.json`. During MIDI generation, status changes to `transcribing`. The completed status includes `midiOutputs` and any non-fatal `transcriptionErrors`.

## Files and directories
`backend/` — Node.js backend (serves UI, handles uploads)<br>
`demucs/` — Demucs worker image (watches uploads, separates audio, generates draft MIDI)<br>
`uploads/` — incoming files (mounted into containers)<br>
`output/` — generated stems, MIDI files, reports, and status JSON files<br>

## Support
If you find this useful, you can support the project:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/pizzu)

## Contributing
Pull requests welcome. Especially if they:

- add more helpful messages (or sarcasm)
- remove unnecessary code
- make the project look more serious than it actually is

## License
MIT
