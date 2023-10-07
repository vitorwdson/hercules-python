#! /usr/bin/bash

./tailwindcss -o ./core/static/vendor/tailwind/bundle.css
python manage.py collectstatic --no-input
