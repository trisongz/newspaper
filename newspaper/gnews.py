"""
Built on https://github.com/ranahaani/GNews/blob/master/gnews/gnews.py
"""
import re
import httpx
import logging
import feedparser

import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup as Soup
from typing import List, Union, Dict
from .gnews_utils import AVAILABLE_COUNTRIES, AVAILABLE_LANGUAGES, TOPICS, BASE_URL, USER_AGENT, GOOGLE_NEWS_REGEX, GNewsArticle, GNewsResult, OrJson
from .article import Article

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

async_httpx = httpx.AsyncClient()

def process_url(item, exclude_websites):
    source = item.get('source').get('href')
    if not all([not re.match(website, source) for website in
                [f'^http(s)?://(www.)?{website.lower()}.*' for website in exclude_websites]]):
        return
    url = item.get('link')
    if re.match(GOOGLE_NEWS_REGEX, url):
        url = httpx.head(url).headers.get('location', url)
    return url


async def async_process_url(item, exclude_websites):
    source = item.get('source').get('href')
    if not all([not re.match(website, source) for website in
                [f'^http(s)?://(www.)?{website.lower()}.*' for website in exclude_websites]]):
        return
    url = item.get('link')
    if re.match(GOOGLE_NEWS_REGEX, url):
        resp = await async_httpx.head(url) #.headers.get('location', url)
        url = resp.headers.get('location', url)
    return url



class GNews:
    """
    GNews initialization
    """
    def __init__(self, language="en", country="US", max_results=20, period='30d', exclude_websites=None, proxy=None):
        self.countries = tuple(AVAILABLE_COUNTRIES),
        self.languages = tuple(AVAILABLE_LANGUAGES),
        self._max_results = max_results
        self._language = language
        self._country = country
        self._period = period
        self._exclude_websites = exclude_websites if exclude_websites and isinstance(exclude_websites, list) else []
        self._proxy = {'http': proxy, 'https': proxy} if proxy else None

    def _ceid(self):
        if self._period: return f'when%3A{self._period}&ceid={self._country}:{self._language}&hl={self._language}&gl={self._country}'
        return f'&ceid={self._country}:{self._language}&hl={self._language}&gl={self._country}'

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = AVAILABLE_LANGUAGES.get(language, language)

    @property
    def exclude_websites(self):
        return self._exclude_websites

    @exclude_websites.setter
    def exclude_websites(self, exclude_websites):
        self._exclude_websites = exclude_websites

    @property
    def max_results(self):
        return self._max_results

    @max_results.setter
    def max_results(self, size):
        self._max_results = size

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, period):
        self._period = period

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, country):
        self._country = AVAILABLE_COUNTRIES.get(country, country)

    def get_full_article(self, url):
        try:
            article = Article(url=url, language=self._language)
            article.build()
        except Exception as error:
            logger.error(error.args[0])
            return None
        return article
    
    async def async_get_full_article(self, url):
        try:
            article = Article(url=url, language=self._language)
            await article.async_build()
        except Exception as error:
            logger.error(error.args[0])
            return None
        return article

    def _clean(self, html):
        soup = Soup(html, features="html.parser")
        text = soup.get_text()
        text = text.replace('\xa0', ' ')
        return text

    def _process(self, item):
        url = process_url(item, self._exclude_websites)
        if url:
            title = item.get("title", "")
            item = {
                'title': title,
                'description': self._clean(item.get("description", "")),
                'published_date': item.get("published", ""),
                'url': url,
                'publisher': item.get("source", {})
            }
            return GNewsResult(**item)
    
    async def _async_process(self, item):
        url = await async_process_url(item, self._exclude_websites)
        if url:
            title = item.get("title", "")
            item = {
                'title': title,
                'description': self._clean(item.get("description", "")),
                'published_date': item.get("published", ""),
                'url': url,
                'publisher': item.get("source", {})
            }
            return GNewsResult(**item)

    def get_news(self, key):
        """
         :return: JSON response as nested Python dictionary.
        """
        if key:
            key = "%20".join(key.split(" "))
            url = BASE_URL + '/search?q={}'.format(key) + self._ceid()
            return self._get_news(url)

    async def async_get_news(self, key):
        """
         :return: JSON response as nested Python dictionary.
        """
        if key:
            key = "%20".join(key.split(" "))
            url = BASE_URL + '/search?q={}'.format(key) + self._ceid()
            return await self._async_get_news(url)

    def get_top_news(self):
        """
         :return: Top News JSON response.
        """
        url = BASE_URL + "?" + self._ceid()
        return self._get_news(url)
    

    async def async_get_top_news(self):
        """
         :return: Top News JSON response.
        """
        url = BASE_URL + "?" + self._ceid()
        return await self._async_get_news(url)

    def get_news_by_topic(self, topic: str):
        f"""
        :params: TOPIC names i.e {TOPICS}
         :return: JSON response as nested Python dictionary.
        """
        topic = topic.upper()
        if topic in TOPICS:
            url = BASE_URL + '/headlines/section/topic/' + topic + '?' + self._ceid()
            return self._get_news(url)

        logger.info(f"Invalid topic. \nAvailable topics are: {', '.join(TOPICS)}.")
        return []
    
    async def async_get_news_by_topic(self, topic: str):
        f"""
        :params: TOPIC names i.e {TOPICS}
         :return: JSON response as nested Python dictionary.
        """
        topic = topic.upper()
        if topic in TOPICS:
            url = BASE_URL + '/headlines/section/topic/' + topic + '?' + self._ceid()
            return await self._async_get_news(url)

        logger.info(f"Invalid topic. \nAvailable topics are: {', '.join(TOPICS)}.")
        return []

    def get_news_by_location(self, location: str):
        """
        :params: city/state/country
         :return: JSON response as nested Python dictionary.
        """
        if location:
            url = BASE_URL + '/headlines/section/geo/' + location + '?' + self._ceid()
            return self._get_news(url)
        logger.warning("Enter a valid location.")
        return []


    async def async_get_news_by_location(self, location: str):
        """
        :params: city/state/country
         :return: JSON response as nested Python dictionary.
        """
        if location:
            url = BASE_URL + '/headlines/section/geo/' + location + '?' + self._ceid()
            return await self._async_get_news(url)
        logger.warning("Enter a valid location.")
        return []


    def _get_news(self, url):
        try:
            if self._proxy:
                proxy_handler = urllib.request.ProxyHandler(self._proxy)
                feed_data = feedparser.parse(url, agent=USER_AGENT, handlers=[proxy_handler])
            else: feed_data = feedparser.parse(url, agent=USER_AGENT)
            return [item for item in map(self._process, feed_data.entries[:self._max_results]) if item]
        except Exception as err:
            logger.error(err.args[0])
            return []
    

    async def _async_get_news(self, url):
        try:
            if self._proxy:
                proxy_handler = urllib.request.ProxyHandler(self._proxy)
                feed_data = feedparser.parse(url, agent=USER_AGENT, handlers=[proxy_handler])
            else: feed_data = feedparser.parse(url, agent=USER_AGENT)
            rez = []
            for i in feed_data.entries[:self._max_results]:
            #    print(i)
                item = await self._async_process(i)
            #    print(item)
                if item: rez.append(item)
            return rez
            #return [item for item in map(await self._async_process, feed_data.entries[:self._max_results]) if item]
        except Exception as err:
            logger.error(err.args[0])
            return []


class GNewsCache:
    api: GNews = None
    min_wc: int = 350
    data: Dict[str, List[Union[GNewsResult, GNewsArticle]]] = {}
    check: set = set()

    @classmethod
    def get_client(cls, **kwargs):
        if not cls.api: cls.api = GNews(**kwargs)
        return cls.api

    @classmethod
    def add_results(cls, query: str, results: List[Union[GNewsResult, GNewsArticle]]):
        if not cls.data.get(query):
            cls.data[query] = []
        if results:
            rez = [r for r in results if r.url not in cls.check]
            for r in rez:
                cls.check.add(r.url)
            cls.data[query].extend(rez)

    @classmethod
    async def build_all(cls):
        """ Builds all items in data into GNewsArticle"""
        build_items = cls.data.items()
        for q, items in build_items:
            logger.info(f'Building {len(items)} items for query:{q}')
            rez = [await i.async_build() if isinstance(i, GNewsResult) else i for i in items]
            rez = [i for i in rez if i.num_words >= cls.min_wc]
            #logger.info(f'Completed {len(rez)} items for query:{q}')
            cls.data[q] = rez
            logger.info(f'Completed {len(cls.data[q])} items for query:{q}')

    @classmethod
    async def async_get(cls, query: str, **kwargs):
        c = cls.get_client()
        rez = await c.async_get_news(key=query)
        if rez: cls.add_results(query, rez)

    @classmethod
    async def async_get_topic(cls, topic: str, **kwargs):
        c = cls.get_client()
        rez = await c.async_get_news_by_topic(topic=topic)
        if rez: cls.add_results(topic, rez)
    
    @classmethod
    async def async_get_top_news(cls, **kwargs):
        c = cls.get_client()
        rez = await c.async_get_top_news()
        if rez: cls.add_results('top_news', rez)
    
    @classmethod
    def get_datalist(cls, filter: List[str] = None) -> List[GNewsArticle]:
        rez = []
        for q, items in cls.data.items():
            if not filter or (q in filter):
                rez.extend(items)
        return rez

    @classmethod
    async def async_dumps(cls, filter: List[str] = None, props: List[str] = None):
        """ dumps all results into jsonlines format"""
        await cls.build_all()
        rez = cls.get_datalist(filter=filter)
        return '\n'.join(r.dumps(props=props) for r in rez) + '\n'
    
    @classmethod
    async def async_save(cls, filepath: str, filter: List[str] = None, props: List[str] = None):
        """ saves all results into jsonlines format"""
        rez = await cls.async_dumps(filter=filter, props=props)
        p = Path(filepath)
        with p.open('a', encoding='utf-8') as writer:
            writer.write(rez)
        logger.info(f'Saved to {p.as_posix()}')

    @classmethod
    def load_from_cache(cls, filepath: str, **kwargs):
        """ Loads from a jsonlines to construct data"""
        p = Path(filepath)
        assert p.exists(), f'{filepath} does not exist'
        if not cls.data.get('cached'): cls.data['cached'] = []
        logger.info(f'Starting cache size: {len(cls.data["cached"])}')
        with p.open('r', encoding='utf-8') as reader:
            for line in reader:
                i = OrJson.loads(line)
                cls.check.add(i['url'])
                cls.data['cached'].append(GNewsArticle(**i))
        logger.info(f'End cache size: {len(cls.data["cached"])}')

    @classmethod
    def load_urls_from_cache(cls, filepath: str, **kwargs):
        """ Loads from a jsonlines to get all the urls"""
        p = Path(filepath)
        with p.open('r', encoding='utf-8') as reader:
            for line in reader:
                i = OrJson.loads(line)
                cls.check.add(i['url'])
        logger.info(f'Total Url Cache: {len(cls.check)}')


