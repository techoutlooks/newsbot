# Getting started with GCP 

Optional, do once per project. 


## Setup GCP CLI locally

- Install and authenticate `gcloud` CLI locally
    ```shell
    curl https://sdk.cloud.google.com | bash
    gcloud init
    ```

- Set few useful env vars before proceeding. \
  Note: Get valid project id from: `gcloud config list`
    ```shell
    
    # newsbot 
    DB_URI='mongodb+srv://techu:techu0910!@cluster0.6we1byk.mongodb.net/scraped_news_db?retryWrites=true&w=majority'
    
    # gcloud
    REGION=europe-west1
    PROJECT_ID=leeram
    BOT_IMAGE_NAME=newsbot:v1
    SERVICE_ACCOUNT=docker-sa
    GCP_KEY_PATH=~/Devl/Projects/Leeram/leeram-51c8a2d9d33a.json
    BUCKET_NAME=leeram-fusebucket
    ```

- Set global env vars
    ```shell
    gcloud config set core/project $PROJECT_ID
    gcloud config set run/region $REGION
    ```


## GCP Service Account (one time)

Goal:

* Create a service account (required to make requests to Google APIs) with necessary permissions.
* Enable required GCP apis

Steps:

1. Create new service account with appropriate permissions,
   associate it with the project.
   Could have also used a single `--role roles/owner` \
   Refs: [1](https://cloud.google.com/sdk/gcloud/reference/projects/add-iam-policy-binding),
         [2](https://cloud.google.com/iam/docs/service-accounts-actas)

    ```shell
   PROJECT_ID=leeram 
    gcloud iam service-accounts create $SERVICE_ACCOUNT
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member "serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
        --role "roles/storage.admin" \
        --role "roles/run.admin" \ 
        --role "roles/storage.objectAdmin"
    ```

2. Create and download service account key.json from CGP's IAM service.
   (preferably outside git repo), and export it locally.
    ```shell
    gcloud iam service-accounts keys create ${GCP_KEY_PATH} \
        --iam-account ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com
   
    export GOOGLE_APPLICATION_CREDENTIALS=${GCP_KEY_PATH}
    ```

## Using Google Cloud CLI (#way)

* Check service account permissions
    ```shell
    gcloud projects get-iam-policy $PROJECT_ID  \
        --flatten="bindings[].members" \
        --format='table(bindings.role)' \
        --filter="bindings.members:${SERVICE_ACCOUNT}"
    ```
  
* Enable required cloud APIs: 
    ```shell
    gcloud services enable \
        artifactregistry.googleapis.com \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        cloudscheduler.googleapis.com
    ```
   
* Create network filesystem using FUSE bucket
    ```shell
    # Creating gs://leeram-fusebucket/...
    gsutil mb -l $REGION gs://$BUCKET_NAME
    ```
  
* Check bucket
    ```shell
    gsutil ls gs://$BUCKET_NAME
    ```
   
## Using Docker (way #2)

Authenticate Docker with the Container Registry service on GCR. \
Refs: [1](https://cloud.google.com/container-registry/docs/advanced-authentication),
[2](https://faun.pub/working-with-google-container-registry-gcr-d6ac0f35a0e8)


```shell 
gcloud auth activate-service-account $SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
	--key-file=$GCP_KEY_PATH

# configure Docker
# alternate way: `gcloud auth configure-docker`
sudo docker login -u _json_key -p "$(cat $GCP_KEY_PATH)" https://gcr.io
```


## Docs:

* [IAM Roles](https://cloud.google.com/storage/docs/access-control/iam-roles)
* [Install gsutil](https://cloud.google.com/storage/docs/gsutil_install)
