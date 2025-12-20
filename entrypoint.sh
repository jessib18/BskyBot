#!/bin/bash
if [ ! -f /persistent_data/timestamp.json ]; then
    cp timestamp.json /persistent_data/timestamp.json
    echo "copied initial timestamp"
fi

cd /app
echo "starte main.py"
python -u main.py 
