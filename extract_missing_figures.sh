#!/usr/bin/env bash
# Corre figure_extractor.py sobre todos los PDFs en pappers/ que aún no tienen _figures
# Loguea éxito/fallo a extraction.log

set -u

PROJECT_DIR="/media/admin/ALMACEN_GRANDE_1/ilovepappers"
PAPPERS="${PROJECT_DIR}/pappers"
SCRIPT="${PROJECT_DIR}/figure_extractor.py"
LOG="${PROJECT_DIR}/extraction.log"
PY="/home/admin/miniconda3/bin/python"

echo "=== Inicio: $(date) ===" | tee -a "$LOG"

cd "$PAPPERS"

count=0
ok=0
fail=0

for pdf in *.pdf; do
    base="${pdf%.pdf}"

    # Saltar archivos de resumen extra
    [[ "$pdf" == resumen_extra_* ]] && continue

    # Saltar si ya tiene _figures
    [ -d "${base}_figures" ] && continue

    count=$((count+1))
    echo "" | tee -a "$LOG"
    echo "[$count] >>> $pdf" | tee -a "$LOG"

    if timeout 600 "$PY" "$SCRIPT" "$pdf" >> "$LOG" 2>&1; then
        ok=$((ok+1))
        echo "    OK" | tee -a "$LOG"
    else
        fail=$((fail+1))
        echo "    FAIL" | tee -a "$LOG"
    fi
done

echo "" | tee -a "$LOG"
echo "=== Fin: $(date) ===" | tee -a "$LOG"
echo "Total procesados: $count | OK: $ok | FAIL: $fail" | tee -a "$LOG"
