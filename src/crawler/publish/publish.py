"""
Utilities collection for publishing news (Post items)
to third-party publishers, including social networks.
"""
import json
import urllib

import aenum
import requests
from urllib3.exceptions import MaxRetryError

from newsutils.conf import get_setting
from newsutils.conf.mixins import PostStrategyMixin
from newsutils.conf.post_item import Post
from newsutils.crawl import Day
from newsutils import conf


__all__ = (
    "DayPublish", "PublishPost", "PublishConfigMixin"
)


# Scrapy command. Enriches `newsutils.TaskTypes` with the publishing task type
# Requires this module being imported first.
aenum.extend_enum(conf.TaskTypes, 'PUBLISH', 'publish')


class PublishConfigMixin:
    """ Config shortcuts for the publishing task """

    publish_url = get_setting("PUBLISH.publish_url")
    auth = get_setting("PUBLISH.auth")
    project_channels = get_setting("PUBLISH.channels")


class PublishPost(PostStrategyMixin, PublishConfigMixin):
    """
    Publish a Post instance to service `leeram-analytics/publishapi`
    using an authenticated POST request (with legit access token).

    TODO: include image links
    """

    def publish(self, post: Post, channels, private=False, *args, **kwargs):
        access_token = self.authenticate(*args, **kwargs)
        headers = {"Authorization": f"Bearer {access_token}"}
        body = {'channels': json.dumps(channels),
                'post': json.dumps(self.format_post(post)),
                'private': private}
        return requests.post(self.publish_url, data=body, headers=headers)

    def format_post(self, post: Post):
        link = post[conf.LINK]
        title, body = (post[self.caption_field], post[self.summary_field]) \
            if post.is_meta else (post[conf.TITLE], post[conf.EXCERPT])

        data = {
            'type': 'Post', 'link': link, 'title': title, 'body': body,
            'category': post[self.category_field], 'tags': post[conf.TAGS]}
        return data

    @staticmethod
    def authenticate(
        auth_url, client_id,
        realm_name, username, password, client_secret=None,
        cacert=None, insecure=None
    ) -> str:
        """
        https://github.com/openstack/python-mistralclient/blob/master/mistralclient/auth/keycloak.py
        """
        access_token_endpoint = (
            "%s/realms/%s/protocol/openid-connect/token" % (auth_url, realm_name))

        verify = None
        if urllib.parse.urlparse(access_token_endpoint).scheme == "https":
            verify = False if insecure else cacert if cacert else True

        body = {
            'grant_type': 'password', 'username': username, 'password': password,
            'client_id': client_id, 'scope': 'openid profile email'}

        if client_secret:
            body['client_secret'] = client_secret,

        try:
            r = requests.post(access_token_endpoint, data=body, verify=verify)
            r.raise_for_status()
        except Exception as e:
            raise Exception("Failed to get access token:\n %s" % str(e))

        return r.json()['access_token']


class DayPublish(PublishPost, Day):
    """
    Helper to publish daily news to multiple publisher networks at once.
    """

    def __init__(self, *args, **kwargs):
        """
        Use `match` kwarg to match only target posts for given day.

        """
        super().__init__(*args, **kwargs)  # sets `self.day` as collection

    def publish_day(self, channels, private=False):
        """
        Publish daily posts to networks.
        `networks=None` to publish to all configured networks.

        :param [str] channels: destination channels
        :param bool private: should create public/private posts?
        """

        messages = []
        queued = 0

        # publish posts, one network at a time. connecting once to a network,
        # and performing subsequent tasks is more efficient
        for post in self.posts:
            try:
                r = self.publish(post, channels, private, **self.auth)
                r.raise_for_status()
                data = r.json()
                if 'queued' in data['status']:
                    queued += 1

            except Exception as e:
                messages.append(str(e))
                if "max retries" in str(e).lower() \
                        or isinstance(e.args[0], MaxRetryError):
                    break

        return queued, messages

