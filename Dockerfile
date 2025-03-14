FROM python:3.12-slim

WORKDIR /bot

COPY /bot .
RUN pip install --no-cache-dir -r requirements.txt

# maybe just copy bot and requirements

CMD ["python", "-m", "main"]