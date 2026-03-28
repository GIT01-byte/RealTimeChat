FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libmagic1 clamav clamav-daemon && rm -rf /var/lib/apt/lists/*

COPY application/clamd_data/* /var/lib/clamav/

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8003