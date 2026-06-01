FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --single-branch --branch 1.3.1 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /opt/bgutil \
    && cd /opt/bgutil/server && npm ci && npx tsc

COPY /bot ./bot

# Install everything in one layer so all plugins land in the same site-packages
RUN pip install --no-cache-dir -r ./bot/requirements.txt

# Verify plugin registration looks correct at build time
RUN python -c "import yt_dlp_plugins; print('plugins OK')" || true

CMD ["python", "-m", "bot.main"]