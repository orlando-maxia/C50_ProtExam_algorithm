#!/usr/bin/env bash
set -euo pipefail

echo "--- Form-like sample ---"
python breast_protocol_extractor.py tests/sample_ocr.txt

echo "--- Plain-text DB sample ---"
python breast_protocol_extractor.py tests/sample_db_plain_text.txt
