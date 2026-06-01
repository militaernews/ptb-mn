FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    npm \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --single-branch --branch 1.3.1 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /opt/bgutil \
    && cd /opt/bgutil/server && npm ci && npx tsc

# Install yt-dlp plugin packages into the image so plugin discovery works
RUN pip install --no-cache-dir \
    yt-dlp==2026.3.17 \
    yt-dlp-get-pot==0.3.0 \
    bgutil-ytdlp-pot-provider==1.3.1

COPY /bot ./bot
RUN pip install --no-cache-dir -r ./bot/requirements.txt

CMD ["python", "-m", "bot.main"]