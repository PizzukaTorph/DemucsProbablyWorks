FROM python:3.10-slim

# System deps required for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Constrain numpy for compatibility, install CPU torch/torchaudio and demucs
RUN pip install --no-cache-dir "numpy<2"
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir git+https://github.com/facebookresearch/demucs

# Copy watcher script and entrypoint
WORKDIR /app
COPY watcher.py /app/watcher.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["./entrypoint.sh"]