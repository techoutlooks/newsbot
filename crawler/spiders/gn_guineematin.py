from news_utils.base.spiders import BasePostCrawler


class GnGuineeMatin(BasePostCrawler):
    """

    # scrapy crawl gn-guineematin -O gn-guineematin.json
    """

    # by `scrapy.spider.Spider`
    name = 'gn-guineematin'
    allowed_domains = ['guineematin.com']
    start_urls = ['https://www.guineematin.com/']

    # by `news_utils.base.spiders.NewsSpider`
    country_code = 'GN'
    language = 'fr'
    post_images_xpath = "//figure/img/@src"
    post_types_xpaths = {
        "featured": '//*[(@id = "tdi_82")]//a | //*[(@id = "tdi_84")]//a',
        "default": '//*[contains(concat( " ", @class, " " ), concat( " ", "tdi_111", " " ))]'
                    '//*[contains(concat( " ", @class, " " ), concat( " ", "td-animation-stack", " " ))]//a',
    }




