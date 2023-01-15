# Getting ready for GCR 

Optional, do once per project. Achieves the following:
* Create service Account (required to make requests to Google APIs)
* Push the app's docker image to their container registry


1. Create new service account with appropriate permissions,
   associate it with the project.
   Could have also used a single `--role roles/owner` \
   Refs: [1](https://cloud.google.com/sdk/gcloud/reference/projects/add-iam-policy-binding)

    ```shell
    gcloud iam service-accounts create local-docker-service 
    PROJECT_ID=leeram 
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member "serviceAccount:${SERVICE_ACCOUNT}@$PROJECT_ID.iam.gserviceaccount.com" \
        --role "roles/storage.admin" \
        --role "roles/run.admin"
    ```

2. Create and download service account key.json from CGP's IAM service.
   (preferably outside git repo), and export it locally.
    ```shell
    gcloud iam service-accounts keys create ${GCP_KEY_PATH} \
        --iam-account ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com
   
    export GOOGLE_APPLICATION_CREDENTIALS=${GCP_KEY_PATH}
    ```

3. Enable cloud APIs: 
    ```shell
    gcloud services enable \
        artifactregistry.googleapis.com \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        cloudscheduler.googleapis.com
    ```
   
4. Optional: authenticate Docker with the Container Registry service on GCR. \
   Refs: [1](https://cloud.google.com/container-registry/docs/advanced-authentication)

    ```shell
    cat ${GCP_KEY_PATH} | docker login -u _json_key --password-stdin https://grc.io
    ```
   
    Alternate method :
    ```shell 
    gcloud auth configure-docker gcr.io
    ```
