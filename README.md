

# arise-newsbot

News crawling and semantic analysis using NLP.

## Features (check the demo )
- Create a spider with few lines of code
- Multiple crawling rules per site, mapping to different post categories.
  Cf. `post_categories_xpaths`
- Detect post content revision => `.version` field of post incremented.
- Bulk crawl news sites with a single command `crawlall`
- Compute posts similarity across posts by all crawled sites (published on same date). 
  `nlp` command.

## TODO
- similarity across docs belonging to several days 


## Dev

### Setup

(Re-)create dev requirements files.
Required before (re-)building Docker the image
```shell
pip-compile requirements/in/prod.txt --output-file requirements/prod.txt 
pip-compile requirements/in/dev.txt  --output-file requirements/dev.txt 


```
Sync dev requirements to venv
```shell
# pip-sync requirements/prod.txt requirements/dev.txt
pip-sync requirements/dev.txt 

```

* Run Scrapy commands individually, eg.:
    ```shell
    cd crawler && python scrapy crawlall && scrapy nlp
    ```

* Or run scheduler script periodically:
    ```shell
    
    python run.py
    ```

### Syntax

Note: -D: for date ranges, -d: for single dates


1. run all spiders
    ```  
     scrapy crawlall \
      [-D from=<%Y-%m-%d> -D to=<%Y-%m-%d>] \ 
      [-d <%Y-%m-%d>] \
    ```

2. update similarity based on thresholds (-t option)
    ```  
     scrapy nlp \
      [-D from=<%Y-%m-%d> -D to=<%Y-%m-%d>] \ 
      [-d <%Y-%m-%d>] \
      [-t siblings=<%f>] [-t related=<%f>]
    ```

### Examples

1. set env and cwd properly
    ```shell
    source venv/bin/activate
    python crawler/commands/nlp.py -t siblings=0.40 -t related=0.2 -d 2022-03-20
    cd backend/newsbot/crawler/
    ```

2. crawl all spiders in the `crawler/spiders` folder
    ```shell
    
    # crawl all posts with regardless their publish time  
    scrapy crawlall
    
    # crall posts matching specified date range (note the -D option)
    scrapy crawlall --loglevel INFO -D from=2022-03-09 -D to=2022-03-09 
    
    # from forever to 2022-04-21
    scrapy crawlall -D to=2022-04-21
    
    # from 2022-04-19 to today
    scrapy crawlall -D from=2022-04-19
    
    # mixed date range and days
    scrapy crawlall -d 2022-04-09 -d 2022-04-10 -d 2022-04-24 -D from=2022-04-19 -D to=2022-04-21          
    ```

3. run NLP tasks

Cf. `TextSummarizer`, `TitleSummarizer`, `Categorizer` models from our
[newsnlp](https://github.com/techoutlooks/newsnlp.git) package (dependency).

`scrapy nlp [similar|summary|metapost] ...` for computing and saving per each post in the db:
- a similarity score vs. other posts published the same day;
  similarity meant for `siblings` or `related` posts of any given post.
- a summary from the post's text and title
- a meta post from the post's siblings, generated by compiling then summarizing the titles and
  texts of all posts.


```shell
# update posts similarity
scrapy nlp similarity -t siblings=0.10 -t related=0.05 -d 2022-05-16

# generate and save a summary for each post
scrapy nlp summary -t siblings=0.10 -t related=0.05 -d 2022-05-16

# generate and save meta posts
scrapy nlp metapost -t siblings=0.10 -t related=0.05 -d 2022-05-16
```


Playing around with dates

```shell
# single dates
scrapy nlp -t siblings=0.40 -t related=0.2 -d 2022-03-07 -d 2022-03-19  

# date range 
scrapy nlp -t siblings=0.40 -t related=0.2 -D from=2022-03-19            

# mixed date range and days
scrapy nlp -t siblings=0.35 -t related=0.15 -D from=2022-03-19 -d 2022-03-02

```

### Docker

Below still to check
```shell
docker-compose run --service-ports newsbot \
  "cd crawler/ && scrapy crawlall && scrapy nlpsimilarity -t siblings=0.4 -t related=0.2 -d 2021-10-22 -d 2021-10-23"
```


### Debugging

#### Strings to look for in logs


2022-03-07 21:15:25 [crawlallcommand] INFO: crawlallcommand >> STARTED crawling news (2021-03-07 to 2021-03-08)
2022-03-07 21:17:46 [crawlallcommand] INFO: crawlallcommand >> DONE crawling news (2021-03-07 to 2021-03-08)


INFO: Dumping Scrapy stats
 'item_scraped_count': 5,



## Prod (GCR, ie. Google Cloud Run)

- Docs:
    [1](https://cloud.google.com/run/docs/execute/jobs)

- Install and authenticate `gcloud` CLI locally
    ```shell
    curl https://sdk.cloud.google.com | bash
    gcloud init
    ```

- Set few useful env vars before proceeding. \
  Note: Get valid project id from: `gcloud config list`
    ```shell
    
    # newsbot 
    CRAWL_DB_URI='mongodb+srv://techu:techu0910!@cluster0.6we1byk.mongodb.net/scraped_news_db?retryWrites=true&w=majority'
    
    # gcloud
    REGION=europe-west1
    PROJECT_ID=leeram
    BOT_IMAGE_NAME=newsbot:v1
    SERVICE_ACCOUNT=local-docker-service
    GCP_KEY_PATH=~/Devl/Projects/ARISE/key.json
    ```

- Set global env vars
    ```shell
    gcloud config set core/project $PROJECT_ID
    gcloud config set run/region $REGION
    ```


### Getting ready for GCR

* Create service Account (required to make requests to Google APIs)
* Push the app's docker image to their container registry


2. Create new service account with appropriate permissions,
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

4. Create and download service account key.json from CGP's IAM service.
   (preferably outside git repo), and export it locally.
    ```shell
    gcloud iam service-accounts keys create ${GCP_KEY_PATH} \
        --iam-account ${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com
   
    export GOOGLE_APPLICATION_CREDENTIALS=${GCP_KEY_PATH}
    ```

5. Authenticate Docker with the Container Registry service on GCR. \
   Refs: [1](https://cloud.google.com/container-registry/docs/advanced-authentication)
    ```shell
    cat ${GCP_KEY_PATH} | docker login -u _json_key --password-stdin https://grc.io
    ```
   
### Run job

1. Enable cloud APIs: 
    ```shell
    gcloud services enable \
        artifactregistry.googleapis.com \
        cloudbuild.googleapis.com \
        run.googleapis.com
    ```
   
2. Build image, eg. `gcr.io/leeram/newsbot:v1`
    ```shell
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$BOT_IMAGE_NAME .
    ```

3. Create the Cloud Run job `newsbot`
    ```shell
    gcloud beta run jobs create newsbot \
      --image gcr.io/$PROJECT_ID/$BOT_IMAGE_NAME \
      --set-env-vars CRAWL_DB_URI=$CRAWL_DB_URI \
      --service-account $SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
      --memory 1Gi
    ```

4. Run the job
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
gcloud beta run executions describe <EXECUTION_NAME>
```

* Update memory
```shell
gcloud beta run jobs update newsbot --memory 1Gi
```

* Update env vars
```shell
gcloud beta run jobs update newsbot  --set-env-vars CRAWL_DB_URI=$CRAWL_DB_URI

```

* Delete job
```shell
gcloud beta run jobs delete newsbot
```



## FIXME

* Move code for fetching post's `.images`, `.top_image` to Pipeline/Middleware
    https://github.com/scrapy/scrapy/issues/2436
    https://doc.scrapy.org/en/latest/topics/spider-middleware.html#scrapy.spidermiddlewares.SpiderMiddleware.process_spider_output
* 
* 


## TODO

#### Anti scraper blocking: 
Refs: [1](https://scrapfly.io/blog/web-scraping-with-scrapy/)


- various plugins for proxy management, eg.:
  - (scrapy-rotating-proxies)[https://github.com/TeamHG-Memex/scrapy-rotating-proxies],
  - (scrapy-fake-useragent)[https://github.com/alecxe/scrapy-fake-useragent], for randomizing user agent headers. 

- Browser emulation:
  - like scrapy-playwright 
  - scrapy-selenium (+GCP): 
    [1](https://youtu.be/2LwrUu9yTAo),
    [2](https://www.roelpeters.be/how-to-deploy-a-scraping-script-and-selenium-in-google-cloud-run/)
- JS support via (Splash)[https://splash.readthedocs.io/en/stable/faq.html]