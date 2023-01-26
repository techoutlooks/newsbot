# TODO

## FIXME

* `scrapy nlp` downloading 2G+ data !
  HINT: ack `newsutils/data/` directory in the Docker bot's image.

  ```
  textPayload: "Terminating task because it has reached the maximum timeout of 600 seconds. To change this limit, see https://cloud.google.com/run/docs/configuring/task-timeout"
  ```


* Move code for fetching post's `.images`, `.top_image` to Pipeline/Middleware
  Currently parses/downloads images event for dup posts uti !
    https://github.com/scrapy/scrapy/issues/2436
    https://doc.scrapy.org/en/latest/topics/spider-middleware.html#scrapy.spidermiddlewares.SpiderMiddleware.process_spider_output


## TODO

#### Bypass scraper blocking

Refs: [1](https://scrapfly.io/blog/web-scraping-with-scrapy/)


- various plugins for proxy management, eg.:
  - (scrapy-rotating-proxies)[https://github.com/TeamHG-Memex/scrapy-rotating-proxies],
  - (scrapy-fake-useragent)[https://github.com/alecxe/scrapy-fake-useragent], for randomizing user agent headers. 

- Browser emulation and scraping dynamic pages (JS) using Scrapy & Selenium
  - scrapy-selenium (+GCP): 
    [1](https://youtu.be/2LwrUu9yTAo),
    [2](https://www.roelpeters.be/how-to-deploy-a-scraping-script-and-selenium-in-google-cloud-run/)
  - scrapy-playwright: Wt's this fella?
  - JS support via (Splash)[https://splash.readthedocs.io/en/stable/faq.html]  \
    Won't do: seem to require running in docker container??
