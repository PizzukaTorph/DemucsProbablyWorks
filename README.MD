# DemucsProbablyWorks

A lightweight, questionably‑engineered wrapper around Demucs. Built for people who “just want to split a track” without reading 40 pages of academic papers or compiling PyTorch at 3 AM.

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

## What it does NOT do
- Improve Demucs
- Be faster than Demucs
- Be smarter than Demucs
- Replace Demucs

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

Note: building the Demucs image can take time and requires network access to download Python packages and models.

## Usage
Open the web UI at: http://localhost:3000

Upload a file and choose a model. The backend will save the file to ./uploads and the Demucs worker will process it, writing stems to ./output.

## Files and directories
``````backend/`````` — Node.js backend (serves UI, handles uploads)<br>
``````demucs/`````` — Demucs worker image (watches uploads/ and writes to output/)<br>
``````uploads/`````` — incoming files (mounted into containers)<br>
``````output/`````` — generated stems and status JSON files<br>

### Status & progress
The worker writes per-file status JSON into output/status/<filename>.json. The web UI polls this file to show progress and logs.

## Support
If you find this useful, you can support the project:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/pizzu)

## Contributing
Pull requests welcome. Especially if they:

add more helpful messages (or sarcasm),
remove unnecessary code, or
make the project look more serious than it actually is.
## License
MIT 