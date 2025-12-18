#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "$SCRIPT_DIR"
sudo docker run --rm -v ${SCRIPT_DIR}/persistent_data:/persistent_data enbot
