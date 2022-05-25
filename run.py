import os
import time
import threading
import schedule
import queue

from news_utils.funcs import get_env_variable

CRAWL_SCHEDULE = get_env_variable('CRAWL_SCHEDULE', 30)


def crawl_job(job_id):
    print(f"`scheduler: running job {job_id}")
    os.system(
        "cd crawler && "
        "scrapy crawlall && "
        "scrapy nlp"
    )


def worker_main():
    print(f"`scheduler: crawl scheduler started - runs every {CRAWL_SCHEDULE} minutes.")
    job_id = 0
    while 1:
        job_id += 1
        job_func = jobqueue.get()
        job_func(job_id)
        jobqueue.task_done()


jobqueue = queue.Queue()
schedule.every(CRAWL_SCHEDULE).seconds.do(jobqueue.put, crawl_job)
schedule.run_all()
worker_thread = threading.Thread(target=worker_main)
worker_thread.start()

while 1:
    schedule.run_pending()
    time.sleep(1)
