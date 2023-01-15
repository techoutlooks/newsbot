import datetime
import os
import time
import schedule

from newsutils.helpers import get_env_variable


# runs only once by default, ie. `CRAWL_SCHEDULE=0`
# TODO: timeit https://stackoverflow.com/a/62905867
# FIXME: faster scraper that ends before the end of schedule period
#   100 pages scraped in 35mn currently !!
# eg. stats for guineenews, guineematin (2):
# 'downloader/request_count': 89,
# 'elapsed_time_seconds': 31429.129115,
CRAWL_SCHEDULE = get_env_variable('CRAWL_SCHEDULE', 0)


def crawl_job():
    print(f"`crawl_job started - runs " + (
        f"every {CRAWL_SCHEDULE} minutes." if CRAWL_SCHEDULE else "once"
    ))
    today = str(datetime.datetime.now().date())
    os.system(
        "cd crawler && "
        f"scrapy crawlall -d {today} && "
        f"scrapy nlp -d {today} -t siblings=.4 -t related=.2"
    )

    # run job only once iff no schedule defined
    if not CRAWL_SCHEDULE:
        return schedule.CancelJob


schedule.every(CRAWL_SCHEDULE).seconds.do(crawl_job)


while True:
    schedule.run_pending()
    time.sleep(1)
