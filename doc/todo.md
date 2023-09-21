# TODO


I. FIXME
-----


### Crawler

* [OK] Dedup `CrawlerRunner` instantiation in `crawlall` command since 
  `scrapy.commands.ScrapyCommand` already wraps a runner subclass as `.crawler_process`.
  Call it as `.crawler_process.crawl(spider, *args, **kwargs)` to run a spider.


### Publish 

* `PublishCmd`: request stats from `leeram-analytics/publishapi` 
* `PublishCmd`: do not publish with same version twice (reject minor changes, cf `newsutils.pipelines`) 
* `PublishCmd`: ensure channels are available before attempting publishing

### DevOps

* Docker container must run wsgi/gunicorn/asyncio, etc. instead of mere ./run.py script



II. Feature request
---------------

* Associate confidence scores (%) with every post
* Voice news

