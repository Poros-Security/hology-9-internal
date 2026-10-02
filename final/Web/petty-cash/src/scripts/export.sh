#!/bin/sh
# Plausible-looking ops script invoked by /internal/sync/export.
# Accepts a format ($1) and a destination ($2); does a trivial placeholder
# "conversion" step. The script itself is not the vulnerability - the
# unsanitized destination reaching the shell via exec() is.
set -u

FORMAT="${1:-csv}"
DESTINATION="${2:-export.csv}"

echo "Preparing accounting export..."
echo "Format: ${FORMAT}"
echo "Writing to staging destination: ${DESTINATION}"
echo "Export sync complete."
