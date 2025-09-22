#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/tmp/e2e"
mkdir -p "$OUT_DIR"

REQ_JSON="$OUT_DIR/request.json"
HDRS_TXT="$OUT_DIR/response_headers.txt"
PDF_OUT="$OUT_DIR/output.pdf"
LOG_TXT="$OUT_DIR/log.txt"

echo "[e2e] Writing request payload" | tee "$LOG_TXT"
cat > "$REQ_JSON" <<'JSON'
{
  "markdown": "# E2E Test\n\nThis is a small test document.\n\n- Bullet\n- List\n",
  "company": "E2E Corp",
  "address": "123 Test Street",
  "phone": "+1 (555) 0100",
  "disclaimer": "E2E test disclaimer"
}
JSON

echo "[e2e] Posting to backend: http://localhost:5002/api/convert" | tee -a "$LOG_TXT"
set +e
curl -s -D "$HDRS_TXT" -H 'Content-Type: application/json' \
  -o "$PDF_OUT" \
  --data-binary @"$REQ_JSON" \
  http://localhost:5002/api/convert
STATUS=$?
set -e

if [ "$STATUS" -ne 0 ]; then
  echo "[e2e] curl failed with status $STATUS" | tee -a "$LOG_TXT"
  exit $STATUS
fi

echo "[e2e] Response headers:" | tee -a "$LOG_TXT"
cat "$HDRS_TXT" | tee -a "$LOG_TXT"

if [ -s "$PDF_OUT" ]; then
  SIZE=$(wc -c < "$PDF_OUT")
  echo "[e2e] PDF saved to $PDF_OUT ($SIZE bytes)" | tee -a "$LOG_TXT"
else
  echo "[e2e] No PDF output written" | tee -a "$LOG_TXT"
  exit 1
fi

echo "[e2e] Done" | tee -a "$LOG_TXT"
