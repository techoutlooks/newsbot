# newsbot

News crawling and semantic analysis using NLP.
Companion code for [scrapy-newsutils](https://github.com/techoutlooks/scrapy-newsutils/).
that demonstrate how to scrape hundreds of websites to a MongoDB collection, filter out ads duplicate and undesirable content, 
run NLP pipelines to gather posts by content affinity, generate titles and summaries, etc.

An improved version is used to scrape news at [Leeram News](https://leeram.today/).
Use the [newspi](https://github.com/techoutlooks/newsapi/) GraphQL server to serve news downloaded by `newsbot`.

Cf. README.md file from package `scapy-newsutils` for a ride on features.

## Features (check the demo )
- Create a spider with few lines of code
- Multiple crawling rules per site, mapping to different post categories.
  Cf. `post_categories_xpaths`
- Detect post content revision => `.version` field of post incremented.
- Bulk crawl news sites with a single command `crawlall`
- Compute posts similarity across posts by all crawled sites (published on same date). 
  `nlp` command.


## Command line usage
 
### Syntax

Notes: 
* `-D`: for date ranges, `-d`: for single dates 
* Commands may also be invoked directly eg.,\
`python crawler/commands/nlp.py -t siblings=0.40 -t related=0.2 -d 2022-03-2`

1. run all spiders
    ```  
     scrapy crawlall \
      [-D from=<%Y-%m-%d> -D to=<%Y-%m-%d>] \ 
      [-d <%Y-%m-%d>] \
    ```

2. Run all NLP tasks:
- update similarity based on thresholds (-t option)
- generate metapost from similar (sibling) posts. 
This involves performing model inference to generate original:
caption, summary and category for any given scraped post.
    ```  
     scrapy nlp \
      [-D from=<%Y-%m-%d> -D to=<%Y-%m-%d>] \ 
      [-d <%Y-%m-%d>] \
      [-t siblings=<%f>] [-t related=<%f>]
    ```

### Examples
  
* Following required chdir to Scrapy project dir
    ```shell
    cd src/crawler
    ```

* Run all spiders, scrape today's posts only.
    ```shell 
    python scrapy crawlall 
    ```

* Perform NLP task on today's posts.
    ```shell
    scrapy nlp
    ```

* Publish given day's posts to all channels 
    ```shell
    scrapy publish facebook,twitter -p -D from=2023-03-21 -M metrics=follows,likes,visits -M dimensions=status,feeds -k publish
    
    ```

* Run all above tasks at once, periodically with 10 minutes interval. \
This runs all spiders, fetches sport news, and run NLP tasks.
    ```shell
    CRAWL_SCHEDULE=10  src/run.py
    ```

### Advanced usage

* Crawl all spiders
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

* Run NLP tasks

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

* Playing around with dates

```shell
# single dates
scrapy nlp -t siblings=0.40 -t related=0.2 -d 2022-03-07 -d 2022-03-19  

# date range 
scrapy nlp -t siblings=0.40 -t related=0.2 -D from=2022-03-19            

# mixed date range and days
scrapy nlp -t siblings=0.35 -t related=0.15 -D from=2022-03-19 -d 2022-03-02
```

## Env vars

Following env vars with respective defaults supported by the project: 

* `newsbot.crawler`
  - DB_URI=mongodb://db:27017/scraped_news_db
  - SIMILARITY_SIBLINGS_THRESHOLD=0.4
  - SIMILARITY_RELATED_THRESHOLD=0.2


* `newsbot.ezines` 
  - TIMEOUT=1 - api requests timeout (seconds)


* `src/run.py` script
  - CRAWL_DAYS_FROM - same as `crawlall -D from=<from-date>`
  - CRAWL_DAYS_TO - same as `crawlall -D to=<to-date>`
  - CRAWL_DAYS - same as `crawlall -d <date>`
  - CRAWL_SCHEDULE=20 - interval (minutes) between crawl+nlp jobs


## Setup

### Requisites

* deps: `newsutils`, `conda`, `MongoDb`
* started MongoDB instance
    ```shell
    docker run --name mongo --restart=unless-stopped -d -p 27017:27017  -v mongodata:/data mongo 
    ```

### Env

1. Setup virtualenv  

* conda

```shell

# iff new env (create)
conda env create -f environment.yml

# iff existing env (update)
conda activate newsbot
conda env update --file environment.yml --prune
```

* venv
  ```shell
  cd newsbot/src/
  source venv/bin/activate
  pip install -U pip-tools
  ```

2. (Re-)create dev requirements files (optional, dev only)
**Important!**: Re-run required before (re-)building Docker the image
    ```shell
    # run from the `src` folder.
    pip-compile --resolver=backtracking requirements/in/prod.txt --output-file requirements/prod.txt 
    pip-compile --resolver=backtracking requirements/in/dev.txt  --output-file requirements/dev.txt 
    ```

3. Sync dev requirements to venv
    ```shell
    # run from `src` folder.
    pip-sync src/requirements/dev.txt 
    # pip-sync requirements/prod.txt requirements/dev.txt
    ```
   
4. Envvars setup

    ```shell
    
    # newsboard frontend url=http://localhost:3100
    export \
      METAPOST_BASEURL='/post' \
      SCRAPY_SETTINGS_MODULE=crawler.settings
    ```


5. Define your scrapers

Define rules for your scrapers through the database or static classes.
Find help [here](https://github.com/techoutlooks/scrapy-newsutils#usage).


## Deploy

### Docker

Build Docker image locally. 

```shell
export TAG=1.0 REGISTRY=localhost:5001
docker build . -t $REGISTRY/newsbot:$TAG # --no-cache --pull
```

Notes: 
* `localhost:5001` is local Docker registry (needed for testing in local KinD Kubernetes cluster)
* Add `--no-cache --pull` to ignore cached and pulled layers.


### Prod

* Getting [ready for GCP](./doc/gcloud-init.md). Optional, do once per project) 
* Deploy to Kubernetes cluster in [GKE](./doc/gke.md)
* Deploy as a [gcloud run job](./doc/cloudrun.md).


## Debugging

* [debugging hints](./doc/debug.md).


## TODO

* [Fixes](./doc/todo.md#fixme).
* [Future](./doc/todo.md#todo).
* Run dev and Docker image in conda rather than venv. cf `newsnlp` dep
