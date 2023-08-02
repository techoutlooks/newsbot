from collections import Counter

import pymongo
from newsutils.conf import TYPE, METAPOST, DIMENSIONS, METRICS, args_from_str, get_setting, validate_fields
from newsutils.crawl import DayCmd
from newsutils.helpers import dotdict

from crawler.publish import PublishConfigMixin, DayPublish, Stats
from newsutils.logging import log_running, NamespaceFormatter

from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError
from scrapy.utils.conf import arglist_to_dict

from daily_query.helpers import mk_date


class PublishCmd(PublishConfigMixin, DayCmd):
    """
    Runs following subtasks sequentially:

    (1) Publishes posts of given type to selected publisher channels
        (this is the default task), then
    (2) Fetches metrics from same publishers (--pull-metrics / -M),
        and save them to the configured database.

    Usage:
        #
        publish facebook,twitter -p -D from=2023-03-21 \
            -M metrics=follows,likes,visits \                   # only specified metrics
            -M dimensions=status,feeds \                        # only specified dimensions
            -k publish                                          # skip task publish

        # all channels
        >>> scrapy publish                                      # today's posts, all channels
        >>> scrapy publish -d 2021-08-28                        # specific day, all channels
        >>> scrapy publish -d 2021-08-28 -d 2021-08-29          # date list, all channels
        >>> scrapy publish -D from=2022-05-20 -D to=2023-03-19  # date range, all channels

        # specific channels, same date options apply
        >>> scrapy publish -N leeram-facebook, leeram-telegram

    """

    # ScrapyCommand overrides
    requires_project = True
    log_prefix = "publish"  # picked up by the logger. cf `LoggingMixin`.

    def short_desc(self):
        return "Update day's (default, today) articles with similarity scores"

    def syntax(self):
        return f'<{"|".join(filter(None, self.project_channels))}> [options]'

    def add_options(self, parser):

        ScrapyCommand.add_options(self, parser)

        # date filter
        parser.add_argument(
            "-D", "--days", dest="days_range", action="append", default=[], metavar="DATE",
            help="posts matching date range; eg. -D from=2022-03-19 [to=2022-04-22]."
                 "no option supplied defaults to today's posts.")
        parser.add_argument(
            "-d", "--day", dest="days_list", action="append", default=[], metavar="DATE",
            help=f"posts for given day only; eg. `-d 2021-06-23. "
                 f"(default: -d {mk_date()})")

        # publish task options
        parser.add_argument(
            "-p", "--private", dest="private", action="store_true",
            help=f"should create public/private posts?; default is True")

        # metrics retrival options
        parser.add_argument(
            "-M", "--pull-metrics", dest="pull_metrics", action="append", default=[],
            metavar="NAME=VALUE",
            help=f"pull publisher-maintained metrics; "
                 f"eg. `-M dimensions=status,feeds -M metrics=follows,likes,visits`.")

        # task filtering options
        parser.add_argument(
            "-k", "--skip-task", dest="skip_tasks", action="append", default=[], metavar="DATE",
            help=f"skip selected subtasks eg. `-k publish -k pull_metrics`. "
                 f"(default: skip none, ie. run all tasks")

    def process_options(self, args, opts):

        ScrapyCommand.process_options(self, args, opts)
        try:
            opts.days_range = arglist_to_dict(opts.days_range)
            opts.pull_metrics = arglist_to_dict(opts.pull_metrics)
        except ValueError as e:
            print(e)
            # FIXME: appropriate UsageError msg.
            raise UsageError("Invalid -D value, use -D from/to=DATE", print_help=False)

    def run(self, args, opts):

        channels = args_from_str(args[0]) if args else None
        channels = validate_fields(channels, self.project_channels)
        skip_tasks = opts.skip_tasks

        # Publish Task
        # ---------------------------------
        # publish to all channels by default,
        # ie., `scrapy publish [options]` without the cmd's network arg
        if "publish" not in skip_tasks:
            self.publish(
                days={'days_from': opts.days_range.get('from'),
                      'days_to': opts.days_range.get('to'),
                      'days': opts.days_list},
                channels=channels,
                private=opts.private,
            )

        # Metrics-related Tasks
        # ---------------------------------
        # fetch & save network-provided metrics to database.
        if "pull_metrics" not in skip_tasks:
            pull_metrics_opts = {DIMENSIONS: None, METRICS: None}
            pull_metrics_opts = {k: args_from_str(opts.pull_metrics.get(k)) for k in pull_metrics_opts}
            if any(pull_metrics_opts.values()):
                self.pull_metrics(channels=channels, **pull_metrics_opts)

    def pull_metrics(self, metrics=None, channels=None, dimensions=None):
        """
        Fetch & Persist (overwrites) network-provided metrics to the db.
        #TODO?: save daily stats (overriden)
        """
        stats = Stats(metrics=metrics, channels=channels)(dimensions, refresh=True)
        stats.save()

    def publish(self, days, channels, private):
        """
        Publish posts matching dates to channels

        :param [str] days: the articles' date, eg. `2021-06-22`
        :param [str] channels: channels to publish to. (pushes to all channels if None)
        :param bool private: should create public/private posts?

        :returns published post counts
        """

        counts = dotdict(requested=0, queued=0)

        fmt = NamespaceFormatter({"from": 'N/A', "to": 'N/A'})
        msg = fmt.format("`scrapy publish {channels}` (docs from {days_from} to {days_to}) +{days}",
                         **days, **{"channels": channels})

        # ensure day correspond to an existing database collection
        collections, counts.requested = self.daily.get_collections(**days)
        days_names = [str(d) for d in collections]
        for day in collections:
            # run per day
            publish_day = lambda cmd, *args, **kwargs: cmd.publish_day(*args, **kwargs)
            queued, day_msgs = log_running(f"publishing {day}'s posts to {channels or 'all channels'}", msg) \
                (publish_day)(self, day, channels, private=private)
            # aggregate stats across all requested days
            counts['queued'] += queued

        msg = "queued ({queued}/{requested}) posts to ({channels}) channels: "\
            "published on: {published_on}."
        self.log_task_ended(msg, **counts, **{'channels': len(channels), 'published_on': days_names})

    def publish_day(self, collection, channels=None, private=False):
        """
        Publish daily posts to channels
        Only `metapost` types, ie., post type includes `metapost` are considered.
        """

        match = {TYPE: {'$regex': METAPOST}}
        p = DayPublish(collection, match=match)
        return p.publish_day(channels, private=private)
