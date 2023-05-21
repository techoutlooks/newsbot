#!/usr/bin/env python

import datetime
import os
import time
import schedule
from functools import reduce

from newsutils.helpers import get_env


# runs only once by default, ie. `CRAWL_SCHEDULE=0`
# TODO: timeit https://stackoverflow.com/a/62905867
# FIXME: faster scraper that ends before the end of schedule period
#   100 pages scraped in 35mn currently !!
# eg. stats for guineenews, guineematin (2):
# 'downloader/request_count': 89,
# 'elapsed_time_seconds': 31429.129115,
today = str(datetime.datetime.now().date())
CRAWL_SCHEDULE = get_env('CRAWL_SCHEDULE', 0)
CRAWL_DAYS = get_env('CRAWL_DAYS', [today])
CRAWL_DAYS_FROM = get_env('CRAWL_DAY_FROM', None)
CRAWL_DAYS_TO = get_env('CRAWL_DAY_TO', None)
SIMILARITY_SIBLINGS_THRESHOLD = get_env('SIMILARITY_SIBLINGS_THRESHOLD', .4)
SIMILARITY_RELATED_THRESHOLD = get_env('SIMILARITY_RELATED_THRESHOLD', .2)


def crawl_job():
    """
    Fetches news and perform NLP tasks every periodically.
    Environment variables:
        * CRAWL_SCHEDULE fetch interval (minutes).
        * CRAWL_DAYS_FROM, CRAWL_DAYS_TO : news date interval
        * SIMILARITY_SIBLINGS_THRESHOLD :
        * SIMILARITY_RELATED_THRESHOLD
    """
    print(f"`crawl_job started - runs " + (
        f"every {CRAWL_SCHEDULE} minutes." if CRAWL_SCHEDULE else "once"))

    # run scrapy-based jobs
    days = reduce(lambda acc, d: "".join([acc, f"-d {d}"]), CRAWL_DAYS, "")
    os.system(
        "cd crawler "
        f"&& scrapy crawlall -D from={CRAWL_DAYS_FROM} -D to={CRAWL_DAYS_TO} {days} "
        f"&& scrapy nlp -D from={CRAWL_DAYS_FROM} -D to={CRAWL_DAYS_TO} {days} \
            -t siblings={SIMILARITY_SIBLINGS_THRESHOLD} -t related={SIMILARITY_RELATED_THRESHOLD} "
        f"&& scrapy publish -D from={CRAWL_DAYS_FROM} -D to={CRAWL_DAYS_TO} {days} "
    )

    # run api-based jobs
    os.system(
        f"python crawler/ezines/sports.py"
    )

    # run job only once iff no schedule defined
    if not CRAWL_SCHEDULE:
        return schedule.CancelJob


schedule.every(CRAWL_SCHEDULE).seconds.do(crawl_job)


while True:
    schedule.run_pending()
    if CRAWL_SCHEDULE == 0:
        break
    time.sleep(1)

