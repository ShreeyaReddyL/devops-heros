#!/usr/bin/env bash
# CampusFix load generator.
#
# Sends real HTTP traffic at the CampusFix API so that:
#   * the Prometheus/Grafana panels have something to plot, and
#   * the Horizontal Pod Autoscaler has CPU pressure to react to.
#
# Usage (Linux, macOS, or Git Bash on Windows):
#   ./scripts/load-test.sh
#   URL=http://localhost:3000/api/tickets REQUESTS=500 ./scripts/load-test.sh
#
# A PowerShell equivalent lives in scripts/load-test.ps1.

set -euo pipefail

URL="${URL:-http://127.0.0.1:8000/api/tickets}"
REQUESTS="${REQUESTS:-200}"

if ! command -v curl >/dev/null 2>&1; then
  echo "error: curl is required but was not found in PATH" >&2
  exit 1
fi

if [ "$REQUESTS" -lt 1 ]; then
  echo "error: REQUESTS must be >= 1" >&2
  exit 1
fi

echo "CampusFix load test"
echo "  target   : $URL"
echo "  requests : $REQUESTS"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

start=$(date +%s)
for _ in $(seq 1 "$REQUESTS"); do
  # Emit "<status> <seconds>" per request; '000' marks a transport failure.
  curl -s -o /dev/null -w '%{http_code} %{time_total}\n' "$URL" >>"$tmp" || echo "000 0" >>"$tmp"
done
end=$(date +%s)

total=$(wc -l <"$tmp" | tr -d ' ')
ok=$(awk '$1 >= 200 && $1 < 400' "$tmp" | wc -l | tr -d ' ')
failed=$((total - ok))
avg=$(awk '{ s += $2 } END { if (NR > 0) printf "%.4f", s / NR; else print "n/a" }' "$tmp")
max=$(awk '{ if ($2 > m) m = $2 } END { if (NR > 0) printf "%.4f", m; else print "n/a" }' "$tmp")
elapsed=$((end - start))

echo
echo "  elapsed    : ${elapsed}s"
echo "  successful : ${ok}"
echo "  failed     : ${failed}"
echo "  avg latency: ${avg}s"
echo "  max latency: ${max}s"

if [ "$failed" -gt 0 ]; then
  echo
  echo "Non-2xx responses seen:"
  awk '$1 < 200 || $1 >= 400 { print "  " $1 }' "$tmp" | sort | uniq -c | sort -rn | head
  exit 1
fi

echo
echo "Load test completed successfully."