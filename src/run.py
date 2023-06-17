#!/usr/bin/env python

# SCRAPY_SETTINGS_MODULE=crawler.settings run.py

import datetime
import os
import shlex
import subprocess
import sys
import time
import schedule
from functools import reduce

from newsutils.helpers import get_env

# runs only once by default, ie. `CRAWL_SCHEDULE=0`
# FIXME: env vars here are redundant vs. `scrapy.utils.project.get_project_settings()`
# TODO: timeit https://stackoverflow.com/a/62905867
# FIXME: faster scraper that ends before the end of schedule period
#   100 pages scraped in 35mn currently !!
# eg. stats for guineenews, guineematin (2):
# 'downloader/request_count': 89,
# 'elapsed_time_seconds': 31429.129115,
today = str(datetime.datetime.now().date())
crawl_schedule = int(get_env('CRAWL_SCHEDULE', 0))
crawl_days = get_env('CRAWL_DAYS', [today])
crawl_days_from = get_env('CRAWL_DAYS_FROM', None)
crawl_days_to = get_env('CRAWL_DAYS_TO', None)
similarity_siblings_threshold = get_env('SIMILARITY_SIBLINGS_THRESHOLD', .4)
similarity_related_threshold = get_env('SIMILARITY_RELATED_THRESHOLD', .2)

#  If passing a single string, either shell must be True (see below) or else
#  the string must simply name the program to be executed without specifying any arguments.
# env = dict(os.environ, SCRAPY_SETTINGS_MODULE='crawler.settings')
cwd = os.getcwd()
# env = {**os.environ, 'SCRAPY_SETTINGS_MODULE': 'crawler.settings', 'PYTHONPATH': ';'.join([*sys.path, cwd])}
run = lambda cmd: subprocess.run(cmd, cwd=cwd)
print('os.getcwd() => ', cwd)
print('sys.path => ', sys.path)


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
        f"every {crawl_schedule} minutes." if crawl_schedule else "once"))

    # run scrapy-based jobs
    days = reduce(lambda acc, d: "".join([acc, f"-d {d}"]), crawl_days, "")

    run(shlex.split(f"scrapy crawlall -D from={crawl_days_from} -D to={crawl_days_to} {days} "))

    run(shlex.split(f"scrapy nlp -D from={crawl_days_from} -D to={crawl_days_to} {days} "
        f"-t siblings={similarity_siblings_threshold} -t related={similarity_related_threshold} "))

    run(shlex.split(f"scrapy publish -D from={crawl_days_from} -D to={crawl_days_to} {days} "))

    # run api-based jobs
    run(shlex.split(f"{sys.executable} crawler/ezines/sports.py"))

    # run job only once iff no schedule defined
    if not crawl_schedule:
        return schedule.CancelJob


schedule.every(crawl_schedule).seconds.do(crawl_job)

while True:
    schedule.run_pending()
    if crawl_schedule == 0:
        break
    time.sleep(1)
