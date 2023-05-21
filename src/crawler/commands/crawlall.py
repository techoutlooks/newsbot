from scrapy.commands import ScrapyCommand
from scrapy.crawler import CrawlerRunner
from scrapy.exceptions import UsageError
from scrapy.utils.conf import arglist_to_dict
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor

from newsutils.conf.mixins import PostConfigMixin
from newsutils.logging import NamespaceFormatter, log_running
from daily_query.helpers import mk_date


class CrawlAllCmd(PostConfigMixin, ScrapyCommand):
    """
    https://gist.github.com/gustavorps/0df8bf6b096ecbdca694dbed96d0a334
    """

    requires_project = True
    runner = CrawlerRunner(get_project_settings())
    spiders = runner.spider_loader.list()
    # log_prefix = "crawling news"

    def short_desc(self):
        return "Running all available spiders in the same process, simultaneously"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_option(
            "-D", "--days", dest="days_range", action="append", default=[], metavar="NAME=VALUE",
            help="articles matching date range; eg. -D from=2022-03-19 [to=2022-04-22]."
                 "no option supplied defaults to today's articles.")
        parser.add_option(
            "-d", "--day", dest="days_list", action="append", default=[], metavar="DAY",
            help=f"articles for given day only; eg. `-d 2021-06-23. "
                 f"(default: -d {mk_date()})")

    def process_options(self, args, opts):

        ScrapyCommand.process_options(self, args, opts)
        try:
            opts.days_range = arglist_to_dict(opts.days_range)
        except ValueError:
            raise UsageError("Invalid -a value, use -a NAME=VALUE", print_help=False)

    def run(self, args, opts):
        self.crawl_all(*args, days={'days_from': opts.days_range.get('from'),
                                    'days_to': opts.days_range.get('to'),
                                    'days': opts.days_list})
        reactor.run()

    @defer.inlineCallbacks
    def crawl_all(self, *args, **kwargs):

        fmt = NamespaceFormatter({"from": None, "to": None})
        msg = fmt.format("crawl_all: docs from {days_from} to {days_to} +{days}", **kwargs['days'])

        for spider in self.spiders:
            # enables passing custom msg to logger, better than
            # @log_running('a static msg ...')
            # def crawl(self, spider, *args, **kwargs):
            #     return self.runner.crawl(spider, *args, **kwargs)
            crawl_task = lambda cmd, *args, **kwargs: \
                cmd.runner.crawl(spider, *args, **kwargs)
            yield log_running(f"crawling {spider}", msg)(crawl_task)\
                (self, spider, *args, **kwargs)

        self.log_task_ended(msg)
        reactor.stop()


