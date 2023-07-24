#!/bin/sh
set -e

exec gunicorn app:app -b "${WEBHOOK_HOST:-0.0.0.0}:${WEBHOOK_PORT:-7788}" -w "${WEBHOOK_WORKERS:-1}" --threads "${WEBHOOK_THREADS:-8}"