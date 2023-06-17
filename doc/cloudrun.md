# Prod (GCR, ie. Google Cloud Run)

First, ensure that [intial requirements](./gcloud-init.md) are satisfied. \
Login to GCP and set default project.
```shell
gcloud auth login
gcloud config set project $PROJECT_ID
```

* `gcloud config get project` checks current project.

### Env setup for GCP

- Set few useful env vars before proceeding. \
  Note: Ensure of correct project id from: `gcloud config list`. 
  Note: `gcloud projects list` to see all projects.
    ```shell
    # newsbot 
    CRAWL_DB_URI='mongodb+srv://techu:techu0910!@cluster0.6we1byk.mongodb.net/scraped_news_db?retryWrites=true&w=majority'
    
    # gcloud
    REGION=europe-west1
    PROJECT_ID=leeram
    IMAGE_NAME=newsbot:v1
    SERVICE_ACCOUNT=docker-sa
    GCP_KEY_PATH=~/Devl/Projects/Leeram/leeram-51c8a2d9d33a.json
    BUCKET_NAME=leeram-fusebucket
    ```

### Upload `newsnlp` pretrained models to [Google Cloud Storage](./gcsfuse.md)

Optional step. Will perform automatically once related bug is fixed in the `newsnlp` library.     

### Create the Cloud run Job (NOT service)

Following commands run for the `src` directory.

1. Build image, ie., `gcr.io/leeram/newsbot:v1` remotely
    - via cmd line

    ```shell
    cp cloudrun.Dockerfile Dockerfile
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME .
    ```
    - via `cloudbuild.yaml`
    https://cloud.google.com/build/docs/configuring-builds/create-basic-configuration
    ```shell
    cat << EOF > cloudbuild.yaml 
   
    # cloudbuild.yaml 
    steps:
    - name: 'gcr.io/cloud-builders/docker'
      args: [ 'build', '-t', 'gcr.io/$PROJECT_ID/newsbot:v1', '.' ]
    images:
      - 'gcr.io/$PROJECT_ID/newsbot:v1'
    EOF    
    ```
    ```shell
    gcloud builds submit --config cloudbuild.yaml .
    ```
   - via Docker (ensure Docker is [configured](./gcloud-init.md#using-docker--way-2-) for GCP)
    ```shell
     docker build --ssh default -t $IMAGE_NAME -f cloudrun.Dockerfile .
     docker tag $IMAGE_NAME gcr.io/$PROJECT_ID/$IMAGE_NAME
     docker push gcr.io/$PROJECT_ID/$IMAGE_NAME
    ```

2. Create scheduled job `newsbot` (runs every 20mn). [cmd ref](https://cloud.google.com/sdk/gcloud/reference/beta/run/jobs/create).
    ```shell
    gcloud beta run jobs create newsbot \
      --region $REGION \
      --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
      --set-env-vars CRAWL_DB_URI=$CRAWL_DB_URI \
      --set-env-vars BUCKET=$BUCKET_NAME \
      --service-account $SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
      --memory 4Gi \
      --max-retries 1 --task-timeout 1200 
    ```

3. Run the job
    ```shell
    gcloud beta run jobs execute newsbot
    ```

### Misc

* Check image
```shell
gcloud container images list-tags gcr.io/$PROJECT_ID/newsbot
```

* Describe the execution
```shell
gcloud beta run jobs executions describe <EXECUTION_NAME>
```

* Update memory
```shell
gcloud beta run jobs update newsbot --memory 4Gi
```

* Update env vars
```shell
gcloud beta run jobs update newsbot \
  --set-env-vars CRAWL_DB_URI=$CRAWL_DB_URI

```

* Delete job
```shell
gcloud beta run jobs delete newsbot
```


## Doc

GCP Refs: 
   [Create Jobs](https://cloud.google.com/run/docs/create-jobs)
   [Execute Jobs](https://cloud.google.com/run/docs/execute/jobs),
   [Quickstart](https://cloud.google.com/run/docs/quickstarts/jobs/build-create-python),
   [Demos](https://github.com/GoogleCloudPlatform/jobs-demos),

Tutorials on running Scrapy bots in GCP
   * [Run a Scrapy spider as GCP cloud function](https://weautomate.org/articles/running-scrapy-spider-cloud-function/)
   * [Deploy a scraping script and Selenium in GCR](https://www.roelpeters.be/how-to-deploy-a-scraping-script-and-selenium-in-google-cloud-run/),