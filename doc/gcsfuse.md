# Storage

## Dev (Docker)

Start dockerized mongodb
```shell
docker run -d -p 27017:27017 --name example-mongo mongo:latest
```


## Prod (Google Cloud Storage)

Assumes gcloud cli is installed, and current project configured.

Upload pretrained models to  GCS bucket.
```shell
# create the following file structure on GCS
# gs://leeram-fusebucket/data/lincoln/
# gs://leeram-fusebucket/data/moussaKam/barthez-orangesum-title/
# gs://leeram-fusebucket/data/moussaKam/barthez/
BUCKET_NAME=leeram-fusebucket
gsutil cp -r ./data gs://$BUCKET_NAME/data
```