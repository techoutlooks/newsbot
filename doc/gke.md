
## Deploy to GKE

1. Assumes project is GCP [ready](gcloud-init.md)
2. Build image -> GCP Artifact Registry (Docker Registry obsolete)

    ```shell
    export TAG=1.0 REGISTRY=localhost:5001
    export REPOSITORY="leeram-docker" PROJECT=leeram
    ```

    ```shell
    cd ..
    # docker build . -t $REGISTRY/newsbot:$TAG --no-cache --pull 
    docker build . -t $REGISTRY/newsbot:$TAG --no-cache \
      && docker tag localhost:5001/newsbot:$TAG europe-west1-docker.pkg.dev/$PROJECT/$REPOSITORY/newsbot:$TAG \
      && docker push europe-west1-docker.pkg.dev/$PROJECT/$REPOSITORY/newsbot:1.0
    ```
   
3. Cleanup
   
   ```shell
   
   # remove all static assets without deleting the bucket
   # all objects and their versions from bucket, use the ``-a`` option
   # large number of objects to remove, use the ``gsutil -m`` option (multi-threading/multi-processing)
   gsutil -m rm gs://leeram-news/**
   ```

## Dry-running the project on local Docker engine.

   * Setup project envs
   
   ```shell
   cat << EOF > ../.env
   DB_URI=mongodb://mongo:27017/scraped_news_db
   CRAWL_SCHEDULE=10
   METAPOST_BASEURL=/post
   EOF
   ```

   * Run the Docker container locally
   
   ```shell
   export TAG=1.0 REGISTRY=localhost:5001

   docker run -d --rm \
      --name newsbot --network bridge --env-file='../.env' \
      -v newsbot-data:/newsbot/data \
   "$REGISTRY/newsbot:$TAG" \
   && docker logs -f  newsbot
   ```
   
   * Cleanup
   
   ```shell
   docker rm newsbot
   ```