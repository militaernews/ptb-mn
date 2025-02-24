FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# maybe just copy bot and reuirements

CMD ["python", "-m", "bot.main"]