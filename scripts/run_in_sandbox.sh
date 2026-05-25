#!/usr/bin/env bash
# Reproduce the AS-vs-control sweep from Sasson/Ho/Samson MSE448,
# inside a fresh Islo sandbox, brokered by Crabbox.
#
# Prereqs:
#   - `crabbox` on $PATH                       (https://github.com/openclaw/crabbox)
#   - `ISLO_API_KEY` exported                  (https://islo.dev settings)
#
# Side effects:
#   - briefly holds one Islo lease (released on EXIT via trap)
#   - writes results.json + pnl_hist.png + sweep.png into ./assets/
set -euo pipefail

: "${ISLO_API_KEY:?export ISLO_API_KEY=ak_... first (https://islo.dev settings)}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
SWEEP="$HERE/sweep.py"
OUT="$REPO/assets"
EPISODES="${EPISODES:-3000}"
IMAGE="${ISLO_IMAGE:-docker.io/library/python:3.12-slim}"

mkdir -p "$OUT"

echo ">> warming lease ($IMAGE)…" >&2
WARM_OUT=$(crabbox warmup --provider islo --islo-image "$IMAGE" 2>&1 | tee /dev/stderr)
LEASE=$(printf %s "$WARM_OUT" | awk '/^leased/{print $2; exit}')
[ -n "$LEASE" ] || { echo "could not parse lease id from warmup output"; exit 1; }

cleanup() {
  echo ">> releasing $LEASE…" >&2
  crabbox stop --provider islo "$LEASE" >/dev/null 2>&1 || true
}
trap cleanup EXIT

SWEEP_B64=$(base64 -i "$SWEEP" | tr -d '\n')

echo ">> running sweep in sandbox ($EPISODES episodes/cell)…" >&2
RUN_LOG=$(mktemp)
crabbox run --provider islo --id "$LEASE" -no-sync -- bash -lc "
set -e
pip install --quiet --disable-pip-version-check matplotlib >/dev/null
mkdir -p /tmp/out
echo $SWEEP_B64 | base64 -d > /tmp/sweep.py
EPISODES=$EPISODES OUT_DIR=/tmp/out python3 /tmp/sweep.py
echo '=====ARTIFACTS====='
cd /tmp/out && tar czf /tmp/out.tgz results.json pnl_hist.png sweep.png && base64 /tmp/out.tgz
" 2>&1 | tee "$RUN_LOG"

echo ">> extracting artifacts…" >&2
awk '/=====ARTIFACTS=====/{flag=1;next}/^islo run summary/{flag=0}flag' "$RUN_LOG" \
  | tr -d '\n\r ' | base64 -d > "$OUT/out.tgz"
tar -xzf "$OUT/out.tgz" -C "$OUT"
rm -f "$OUT/out.tgz" "$RUN_LOG"

echo ">> wrote:"
ls -lh "$OUT"/results.json "$OUT"/pnl_hist.png "$OUT"/sweep.png
