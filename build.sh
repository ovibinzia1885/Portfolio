#!/usr/bin/env bash
# Render build step: runs on every deploy (after each push to main).
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
