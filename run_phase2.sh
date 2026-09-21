#!/bin/bash
# Every docket on identical final code, smallest first so a failure is cheap.
cd ~/dev/comment-counts
export COMMENT_COUNTS_BUCKET=comment-counts-ff734f09
export PYTHONPATH=src
for d in OSHA-2010-0034 EPA-HQ-OAR-2021-0317 EPA-HQ-OAR-2013-0602 FWS-HQ-ES-2018-0006 FDA-2021-N-1349 ED-2021-OCR-0166; do
  echo "=== $d $(date +%H:%M:%S) ==="
  .venv/bin/python src/run_docket.py "$d" > "out/final-$d.json" 2> "out/final-$d.log"
  if [ -s "out/final-$d.json" ]; then echo "  ok"; else echo "  FAILED"; fi
done
echo "ALLDONE"
