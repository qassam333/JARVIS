#!/bin/bash
cd /home/deep/BACKUP/GG\ POJECT/GGjarvis/JARVIS
source .venv/bin/activate
exec uvicorn jarvis.dashboard.backend.main:app --host 0.0.0.0 --port 8080
