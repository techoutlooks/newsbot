from news_utils.base.spiders import BasePostCrawler


class GnAfricaGuinee(BasePostCrawler):
    """

    # scrapy crawl gn-africaguinee -O gn-africaguinee.json
    """

    # by `scrapy.spider.Spider`
    name = 'gn-africaguinee'
    allowed_domains = ['africaguinee.com']
    start_urls = ['https://www.africaguinee.com/']

    # by `news_utils.base.spiders.NewsSpider`
    country_code = 'GN'
    language = 'fr'
    post_images_xpath = "//figure/img/@src"
    post_types_xpaths = {
        "featured": '//*[contains(concat( " ", @class, " " ), concat( " ", "views_slideshow_pager_field_item", " " ))]//a',
        "default": '//*/div/div/div/div/div/h3//a',
    }

    # days_from = '2022-04-19'
    # days_to = '2022-04-25'
    # days = ['2022-04-12', '2022-04-09']




