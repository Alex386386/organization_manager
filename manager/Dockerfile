FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc g++ libgeos-dev libpq-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY requirements.txt ./

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]