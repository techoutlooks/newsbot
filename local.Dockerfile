# Local KinD Cluster (Dev)
# ------------------------
#   export TAG=1.0 REGISTRY=localhost:5001
#   docker build . -f local.Dockerfile --ssh default -t $REGISTRY/newsbot:$TAG
#   docker push $REGISTRY/newsbot:$TAG
#   docker run -v newsbot-data:/newsbot --network host --name newsbot $REGISTRY/newsbot:$TAG
#
# GKE Cluster (Prod)
# ------------------
#docker tag $REGISTRY/newsbot:1.0 europe-west1-docker.pkg.dev/$PROJECT/$REPOSITORY/newsbot:1.0
#docker push europe-west1-docker.pkg.dev/$PROJECT/$REPOSITORY/newsbot:1.0

# Cloud Run (Old)
# ---------------
#   gcloud builds submit --tag gcr.io/$PROJECT_ID/newsbot:$TAG .
#   gcloud run deploy newsbot --image gcr.io/$PROJECT_ID/newsbot:$TAG \
#       --region us-central1 --platform managed --allow-unauthenticated \
#       --update-env-vars DB_URI=$DB_URI --quiet
#

FROM python:3.9 as deps
WORKDIR /newsbot
ENV PYTHONUNBUFFERED=1
# Install packages, etc.
COPY src/requirements/prod.txt ./requirements.txt
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /newsbot/wheels -r requirements.txt


FROM python:3.9-slim
WORKDIR /newsbot
COPY --from=deps /newsbot/wheels /wheels
COPY --from=deps /newsbot/requirements.txt .
RUN pip install --no-cache /wheels/*
# Copy app code
COPY src/crawler ./crawler
COPY src/scrapy.cfg .
COPY src/run.py  .
# `newsnlp` dependency expects envs `DATA_DIR`, `CACHE_DIR`
# as resp. the data and cache dirs for pretrained models
ENV DATA_DIR /newsbot/data
ENV CACHE_DIR $DATA_DIR/.cache
RUN mkdir -p $CACHE_DIR
VOLUME $DATA_DIR


# Disable self-scheduling tasks by default. Might be achieved via k8s.
CMD ["python", "run.py"]
