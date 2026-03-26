FROM python:3.13-slim

WORKDIR /app

COPY /bot ./bot
RUN pip install --no-cache-dir -r ./bot/requirements.txt

CMD ["python", "-m", "bot.main"]