"""
Fetch & Save metrics from Publishers channels.
[Dimensions and metrics](https://support.google.com/analytics/answer/1033861?hl=en#zippy=%2Cin-this-article)
"""
import abc
import hashlib
from collections import defaultdict
from datetime import datetime
from functools import reduce
from typing import Callable, Mapping

import scrapy
from bson import ObjectId
from daily_query.mongo import Collection
from itemadapter import ItemAdapter

from newsutils import helpers as h
from newsutils.conf import \
    mixins, get_setting, validate_fields, \
    NETWORK, MODIFIED_TIME, PUBLISH_TIME, DIMENSION


__all__ = (
    "FetchMetricsMixin", "SaveMetricsMixin", "BaseStats", "Stats", "Metrics", "mkstats",
    "select_mappings", "select_fields",
    "default_metric_reducer"
)


# pull useful live settings
project_dimensions = get_setting("PUBLISH.dimensions")
project_metrics = get_setting("PUBLISH.metrics")
project_channels = get_setting("PUBLISH.channels")


# default reducer: sums up queried fields' values
# also works like the identity function for 1D-iterables
# regardless of the metric's scale of measurement (bool, int, str, ...).
# cf. constants.STATUS_FIELDS
default_metric_reducer = lambda metric, field_value: \
    metric + field_value


def select_mappings(
        src,                            # look for results here
        channel, metric=None,           # picks fields required by channel query
        metrics=None, channels=None,    # pre-filters by metrics, channels
) -> [str, list[str], Callable]:
    """
    Get metrics query fields by dimension and channel.
    Returns: iterable of triplets mappings.

    :param Mapping src: dimension mapping to lookup, for metric->fields conversion.
    :param str channel: filter by channel
    :param str metric: filter by metric. `None` to return fields for all metrics
    :param list[str] metrics: initial metrics to select from
    :param list[str] channels: initial channels to select from.
    """

    # channel param is crucial
    validate_fields([channel], channels)

    # lambda for channel filtering
    selected_networks = set(channels).intersection([channel])
    filter_networks = lambda triplets: \
        filter(lambda triplet: triplet[0] in selected_networks, triplets)

    # filter fields mappings (triplets) by metrics and channels
    selected_metrics = [metric] if metric else metrics
    fields_list = filter(lambda _: _[0] in selected_metrics, src.items())
    fields_list = h.flatmap(filter_networks, dict(fields_list).values())

    # returns flattened triplets mappings
    return iter(fields_list)


def select_fields(*args, **kwargs) -> list[str]:
    """ Gather fields for possibly many metrics to query from given channel,
    in the given dimension (pointed to by the `src` arg).
    Same params as `select_mappings()`.
    """
    triplets = select_mappings(*args, **kwargs)
    fields = reduce(lambda v, triplet: v + triplet[1], triplets, [])
    return fields


# Initialises a stats dict as a 3D tensor (channel, dimension, N-metrics)
# >>> stats['status']['facebook']  #  {'follows': 0, 'likes': 0, 'visits': 0}
mkstats = lambda data: dict(**{
    n: {d: {m: (h.getdeep(data, ".".join([n, d, m])) if data else 0) for m in project_metrics}
        for d in project_dimensions} for n in project_channels
})

# Metric class, a per-channel 1D (vector) statistic
# as a `scrapy.Item` class. dynamic initialisation allows for
# configuring metrics dynamically.
Metrics = type("Metrics", (scrapy.Item,), {
    **{f: scrapy.Field() for f in project_metrics},
    get_setting('DB_ID_FIELD'): scrapy.Field(),
    DIMENSION: scrapy.Field(),
    NETWORK: scrapy.Field(),
    PUBLISH_TIME: scrapy.Field(),
    MODIFIED_TIME: scrapy.Field()
})


class FetchMetricsMixin(mixins.PostStrategyMixin):
    """
    Fetch metrics for all publisher channels along multiple dimensions.
    Cf. `settings['PUBLISH']['metrics'|'channels'|'dimensions']`,
    for pre-configured values.

    - channels, eg. "facebook", "twitter".
    - dimensions, eg. "status" -> channel page status, "feed" -> posts, tweets, etc.
    - metrics, eg. "follows", "likes", "visits".
    """

    def get_stats(self, dimensions=None):
        """
        All channels stats across all dimensions.

        :param [str] dimensions: valid stats dimensions
            eg. `status`, `feed`, `insights`, `ratings`, ...
            cf. `constants.DIMENSIONS` for default dimensions.

        :returns: 3D tensor (channel, dimension, metric) feg.,
            {
                # metrics for `status` dimension
                "status": {
                    "facebook": { "follows": 5211, "likes": 118, "visits: 102379 },
                    "twitter": { "follows": 5211, "likes": 118, "visits: 102379 },
                }
                ...
            }
        """
        stats = defaultdict(dict)
        # query metrics per dimension and channel
        for channel in self.channels:
            for dimension in validate_fields(dimensions, project_dimensions):
                stats[channel][dimension] = self.fetch(channel, dimension)

        return stats

    def fetch(self, channel, dimension) -> Metrics:
        """
        Fetches metrics along a dimension, from channel.
        Issues a single request per dimension and channel,
        a dimension corresponding to a method to call on `BasePage` class instances,
        that issues the actual fetch request to a Publisher's channel. Same method name
        for all channels. eg., `get_status()`, `get_feed()`....

        :param str metrics: stat metrics to query  eg., `follows`, `likes`, `visits'
            cf. `settings.DIMENSIONS` for supported dimensions.

        :param str channel: channel to query
        :param str dimension: dimension to fetch
        """
        metrics = defaultdict(int)

        # gather all metrics `select_fields(metric=None,...)` to fetch
        # from the channel respective to the specified dimension.
        # `edge_method`: `BasePage.get_*()` method that call the API endpoint (edge)
        src = self.settings["PUBLISH"]["%s_fields" % dimension.lower()]
        fields = select_fields(src, channel, metrics=self.metrics, channels=self.channels)
        edge_method = "get_%s" % dimension
        params = {"fields": fields}

        # fetches all metrics at once
        # eg. return, { "followers_count": 5211, "fan_count": 118, "were_here_count: 102379 }
        raw_metrics = getattr(self.apis[channel], edge_method)(**params)

        # converts raw results -> stat metrics
        # applies optional reducer function
        for metric in self.metrics:
            _, fields, reducer = next(select_mappings(
                src, channel, metric, metrics=self.metrics, channels=self.channels))
            values = [raw_metrics[f] for f in fields]
            reducer = reducer or default_metric_reducer
            metrics[metric] = reduce(reducer, values)
            metrics[NETWORK] = channel
            metrics[DIMENSION] = dimension

        return Metrics(metrics)


class SaveMetricsMixin:
    """
    Save channel metrics (`self.stats`) to the database.
    Collection name: settings.PUBLISH["collection"], defaults to `publish`.
    Required bases: `BaseStats`

    Usage:
        class SaveMetrics(SaveMetricsMixin, BaseStats):
            pass
    """

    # db collection cache
    _collection = None

    @property
    def collection(self):
        name = get_setting("PUBLISH.collection")
        return self._collection or \
            Collection(collection=name, db_or_uri=get_setting("DB_URI"))

    def save(self, overwrite=True):
        """
        Save channel stats to db collections by the dimension name.
        Each database row stores per-channel metrics as with timestamp information.
        Collections are named like so: `<module_name>_*` eg. "publish_status", "publish_feed"

        :param bool overwrite: insert a new record every time if True,
            else update metrics for channel

        TODO: if overwrite, insert no more than 1 record per metric/dimension per day
        """

        # TODO: proper validation for `self.stats`, eg. shape, ...
        assert self.stats, "Invalid `.stats`. Did you fetch stats yet?"

        # metrics saved counts: channel x dimension
        saved = dict(modified=defaultdict(lambda: defaultdict(int)),
                     matched=defaultdict(lambda: defaultdict(int)),
                     total=defaultdict(lambda: defaultdict(int)))

        log_msg = lambda detail: \
            f"saving channel metrics from channels {self.channels}: " \
            f"{detail}"

        self.log_started(log_msg, '...')

        try:
            for channel in self.stats:
                for dimension, metrics in self.stats[channel].items():

                    # save metrics for channel
                    # generate predictable database oid from dimension name
                    # TODO: ensure channel call had returned `publish_time`
                    adapter = ItemAdapter(metrics)
                    _id = hashlib.shake_128(f"{dimension}{channel}".encode('utf8')).digest(12)
                    _id = ObjectId(_id if overwrite else None)
                    adapter.update({
                        self.db_id_field: _id,
                        PUBLISH_TIME: None,                 # channel's time
                        MODIFIED_TIME: str(datetime.now())  # our time
                    })
                    r = self.collection\
                        .update_one({'_id': {'$eq': _id}},
                                    {"$set": adapter.asdict()}, upsert=True)

                    # update write counts
                    saved["modified"][channel][dimension] += r.modified_count
                    saved["matched"][channel][dimension] += r.matched_count
                    saved["total"][channel][dimension] += 1

            # log saved counts for all channels
            detail = ", ".join([
                f"{channel}=%s/%s/%s" % (
                    sum(saved["modified"][channel].values()),
                    sum(saved["matched"][channel].values()),
                    sum(saved["total"][channel].values()),
                ) for channel in project_channels])
            self.log_ok(log_msg, detail)

        except Exception as exc:
            self.log_failed(log_msg, exc, '')

        return saved


class BaseStats(mixins.BaseConfigMixin):
    """
    Contract for building a metrics management facility
    across multiple Publisher channels, eg. Facebook, Instagram, Twitter, etc.

    Stats: metrics collection.
    Basic contract:
        `.get_stats()` -> pull metrics from publisher's api into `.stats` instance attr.
        `.save()`      -> saves `. to the database
    """

    apis = {}

    def __init__(self, channels=None, metrics=None):

        # only selected channels and metrics
        self.channels = validate_fields(channels, project_channels)
        self.metrics = validate_fields(metrics, project_metrics)

        # initialises channel apis with default settings
        for backend, channel in get_backends(self.channels):
            self.apis[channel] = backend()

        # stats to return
        self.stats = defaultdict(dict)

    def __call__(self, dimensions=None, refresh=False):
        """
        Get or refresh latest channel stats query.
        """
        if not self.stats or refresh:
            self.stats = self.get_stats(dimensions)
        return self

    @abc.abstractmethod
    def get_stats(self, dimensions=None):
        """
        All channels stats across all dimensions.
        cf. `settings.DIMENSIONS` for pre-configured dimensions.
        """
        pass

    @abc.abstractmethod
    def save(self):
        """ Save per-channel stats to collection by the channel name. """
        pass


class Stats(SaveMetricsMixin, FetchMetricsMixin, BaseStats):
    """
    Fetch and save statistics for all channels to the database
    Usage:
        # save all metrics and dimensions across all channels
        >>> stats = Stats()().save()

        # only selected dimensions/metrics, channels
        >>> dimensions=["status"]
        >>> metrics = ["follows", "likes", "visits"]
        >>> channels = ["facebook", "twitter"]
        >>> stats = Stats(channels, metrics)()
        >>> stats = Stats().get_stats(dimensions=dimensions)
    """
    pass
