#!/usr/bin/env python
"""
Runs only once by default, ie. `CRAWL_SCHEDULE=0`
Takes abt 10mn for 100 posts on GKE.
TODO: timeit https://stackoverflow.com/a/62905867

Example start:

SCRAPY_SETTINGS_MODULE=crawler.settings \
POSTS=metapost_baseurl=http://localhost:3100/post \
run.py
"""

import datetime
import os
import shlex
import subprocess
import sys
import time
import schedule
from functools import reduce

from newsutils.helpers import get_env


today = str(datetime.datetime.now().date())


# Crawl params
# ------------------------------------------------------------------------------
crawl_schedule = int(get_env('CRAWL_SCHEDULE', 0))
crawl_days = get_env('CRAWL_DAYS', [today])
crawl_days_from = get_env('CRAWL_DAYS_FROM', None)
crawl_days_to = get_env('CRAWL_DAYS_TO', None)


# Envs
# ------------------------------------------------------------------------------

# AppSettings overrides
appsettings = {
    "POSTS": "metapost_baseurl=/post,"
             "similarity_siblings_threshold=.19,similarity_related_threshold=.09,"
             "nlp_uses_excerpt=true,summary_minimum_length=49",
    "SPORTS": "rate_limit=3,fetch_limit=49,timeout=1",
}


# Shell
# ------------------------------------------------------------------------------
cwd = os.getcwd()
env = {'SCRAPY_SETTINGS_MODULE': 'crawler.settings', 'PYTHONPATH': cwd}
env.update({**appsettings, **os.environ})

#  If passing a single string, either shell must be True (see below) or else,
#  the string must simply name the program to be executed without specifying any args.
run = lambda cmd: subprocess.run(cmd, cwd=cwd, env=env)


def crawl_job():
    """
    Fetches news and perform NLP tasks every periodically.
    Environment variables:
        * CRAWL_SCHEDULE: fetch interval (minutes).
        * CRAWL_DAYS_FROM, CRAWL_DAYS_TO : news publication date interval match
        * SIMILARITY_SIBLINGS_THRESHOLD :
        * SIMILARITY_RELATED_THRESHOLD : min
        * SUMMARY_MIN_LEN
    """
    print(f"`crawl_job started - runs " +
          (f"every {crawl_schedule} minutes." if crawl_schedule else "once"))

    # run scrapy-based jobs
    days = reduce(lambda acc, d: "".join([acc, f"-d {d}"]), crawl_days, "")

    run(shlex.split(
        f"scrapy crawlall -D from={crawl_days_from} -D to={crawl_days_to} {days} "))

    run(shlex.split(
        f"scrapy nlp -D from={crawl_days_from} -D to={crawl_days_to} {days} "
    ))

    run(shlex.split(
        f"scrapy publish -D from={crawl_days_from} -D to={crawl_days_to} {days} "))

    # run api-based jobs
    run(shlex.split(
        f"{sys.executable} {cwd}/crawler/ezines/sports.py"))

    # run job only once iff no schedule defined
    if not crawl_schedule:
        return schedule.CancelJob


schedule.every(crawl_schedule).seconds.do(crawl_job)

while True:
    schedule.run_pending()
    if crawl_schedule == 0:
        break
    time.sleep(1)
