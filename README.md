# leeram-newsbot

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


### Requirements

* deps: `pip-tools==6.6.2`, `click=7.1.2` 

### Setup

Install pip-tools
```shell
pip install -U pip-tools
```

(Re-)create dev requirements files. 
**Important!**: Re-run required before (re-)building Docker the image
```shell
# run from the `src` folder.
pip-compile --resolver=backtracking requirements/in/prod.txt --output-file requirements/prod.txt 
pip-compile --resolver=backtracking requirements/in/dev.txt  --output-file requirements/dev.txt 


```
Sync dev requirements to venv
```shell
# run from `src` folder.
pip-sync src/requirements/dev.txt 
# pip-sync requirements/prod.txt requirements/dev.txt
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
CRAWL_SCHEDULE=20 # runs every 20mn
docker-compose run --service-ports newsbot \
  "cd crawler/ && scrapy crawlall && scrapy nlpsimilarity -t siblings=0.4 -t related=0.2 -d 2021-10-22 -d 2021-10-23"
```


## Debugging

* [debugging hints](./doc/debug.md).


## Prod

* Getting [ready for GCP](./doc/gcloud-init.md). Optional, do once per project) 
* Run project as a [gcloud job](./doc/gcloud.md).


## TODO

* [Fixes](./doc/todo.md#fixme).
* [Future](./doc/todo.md#todo).
* Run dev and Docker image in conda rather than venv. cf `newsnlp` dep
