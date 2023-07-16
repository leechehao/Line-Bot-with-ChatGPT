#!/bin/sh
set -e

exec gunicorn app:app -b "${HOST:-0.0.0.0}:${PORT:-7788}" -w "${WORKERS:-1}" --threads "${THREADS:-8}"