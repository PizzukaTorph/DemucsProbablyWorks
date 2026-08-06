FROM python:3.10-slim

# System deps required for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install the CPU audio stack.
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir "numpy<2"
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir git+https://github.com/facebookresearch/demucs

COPY requirements-transcription.txt /app/requirements-transcription.txt
RUN pip install --no-cache-dir -r /app/requirements-transcription.txt

# Copy worker and transcription sources.
COPY watcher.py /app/watcher.py
COPY transcribe.py /app/transcribe.py
COPY transcription /app/transcription
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh /app/transcribe.py

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["./entrypoint.sh"]
