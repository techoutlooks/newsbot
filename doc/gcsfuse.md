# Storage

## Dev (Docker)

Start dockerized mongodb
```shell
docker run -d -p 27017:27017 --name example-mongo mongo:latest
```


## Prod (Google Cloud Storage)

Assumes `gcloud` CLI is installed, and current project configured.

Upload pretrained NLP models to Cloud Storage bucket.
retrained NLP models are required by the `newsnlp` dependency. They are downloaded by the library if not
at the `./data` subdir of the consuming project. Caching them saves needless download requests and costs
with the Cloud Run Service model.

```shell
# create the following file structure on GCS
# gs://leeram-fusebucket/data/lincoln/
# gs://leeram-fusebucket/data/moussaKam/barthez-orangesum-title/
# gs://leeram-fusebucket/data/moussaKam/barthez/
BUCKET_NAME=leeram-fusebucket
gsutil cp -r ./data gs://$BUCKET_NAME/data
```