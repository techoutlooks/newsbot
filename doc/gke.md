
## Deploy to GKE

1. Assumes project is GCP [ready](gcloud-init.md)
2. Build image -> GCP Artifact Registry (Docker Registry obsolete)

    ```shell
    export TAG=1.0 REGISTRY=localhost:5001
    export REPOSITORY="leeram-docker" PROJECT=leeram
    ```

    ```shell
    cd ..
    #docker build . -t $REGISTRY/newsbot:$TAG --no-cache --pull \
    docker build . -t $REGISTRY/newsbot:$TAG \
      && docker tag localhost:5001/newsbot:$TAG europe-west1-docker.pkg.dev/$PROJECT/$REPOSITORY/newsbot:$TAG \
      && docker push europe-west1-docker.pkg.dev/$PROJECT/$REPOSITORY/newsbot:1.0
    ```

3. Dry-running the project on local Docker engine.

   * Setup project envs
   
   ```shell
   cat << EOF > ../.env
   CRAWL_DB_URI=mongodb://mongo:27017/scraped_news_db
   CRAWL_SCHEDULE=10
   METAPOST_BASEURL=/posts
   EOF
   ```

   * Run the Docker container locally
   
   ```shell
   docker run -d --rm \
      --name newsbot --network bridge --env-file='../.env' \
      -v newsbot-data:/newsbot/data \
   "$REGISTRY/newsbot:$TAG"
   ```
   
   * Cleanup
   
   ```shell
   docker rm newsbot
   ```