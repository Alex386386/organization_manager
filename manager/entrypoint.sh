#!/bin/sh

echo "Waiting for postgres..."
sleep 10
python setup_elasticsearch.py
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 8000