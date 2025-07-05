#!/bin/zsh

echo ".............. Starting server ................"
uvicorn main:app --host 0.0.0.0 --port 8000