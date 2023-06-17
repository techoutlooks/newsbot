# Local:
#   DOCKER_IMAGE=newsbot:v1
#   CRAWL_DB_URI=mongodb+srv://techu:<password>@cluster0.6we1byk.mongodb.net/scraped_news_db/?retryWrites=true&w=majority
#   docker build --ssh default -t $DOCKER_IMAGE -f cloudrun.Dockerfile .
#   docker run -v newsbot-data:/newsbot --network host --name newsbot $DOCKER_IMAGE
# GCP
#   gcloud builds submit --tag gcr.io/$PROJECT_ID/$DOCKER_IMAGE .
#   gcloud run deploy newsbot --image gcr.io/$PROJECT_ID/$DOCKER_IMAGE \
#       --region us-central1 --platform managed --allow-unauthenticated \
#       --update-env-vars CRAWL_DB_URI=$CRAWL_DB_URI --quiet
#
FROM python:3.9

# Cloud Storage FUSE with Cloud Run
# https://cloud.google.com/run/docs/tutorials/network-filesystems-fuse
# =========

# Install system dependencies
RUN set -e; \
    apt-get update -y && apt-get install -y \
    tini \
    lsb-release; \
    gcsFuseRepo=gcsfuse-`lsb_release -c -s`; \
    echo "deb http://packages.cloud.google.com/apt $gcsFuseRepo main" | \
    tee /etc/apt/sources.list.d/gcsfuse.list; \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key add -; \
    apt-get update; \
    apt-get install -y gcsfuse \
    && apt-get clean

# Set fallback mount directory for gcloud storage
ENV MNT_DIR /mnt/gcs


# This App
# =========

ENV APP_HOME /newsbot
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# dep `newsnlp`: cache & data dirs for pretrained models
ENV CACHE_DIR ${MNT_DIR}/.cache
ENV DATA_DIR ${MNT_DIR}/data

# Copy code to container image
COPY src/requirements/prod.txt ./requirements.txt
COPY src ./

# Install app packages, etc.
RUN python -m pip install pip-tools
RUN python -m piptools sync

# Generate script that mounts the GCS bucket
# https://www.docker.com/blog/introduction-to-heredocs-in-dockerfiles/
COPY <<EOF gcsfuse_run.sh
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
EOF

# Ensure the script is executable
RUN chmod +x $APP_HOME/gcsfuse_run.sh

# Use tini to manage zombie processes and signal forwarding
# https://github.com/krallin/tini
ENTRYPOINT ["/usr/bin/tini", "--"]

# Pass the startup script as arguments to Tini
#CMD [ "sh", "-c", "echo $APP_HOME/gcsfuse_run.sh"]
CMD ["/newsbot/gcsfuse_run.sh"]