#!/usr/bin/env bash
set -eo pipefail

# Create mount directory for service
mkdir -p $MNT_DIR

echo "gcsfuse > mounting bucket $BUCKET."
gcsfuse --debug_gcs --debug_fuse $BUCKET $MNT_DIR
echo "gcsfuse > mounting completed: $BUCKET -> $MNT_DIR."

# Run crawlers and nlp tasks only once
# Specifically set scheduler on Cloud Run for periodic execution
exec python run.py &

# Exit immediately when one of the background processes terminate.
wait -n