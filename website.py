from collections import OrderedDict
from urllib.parse import urlparse, urlunparse
import asyncio

from bs4 import BeautifulSoup
import aiohttp
import fire
import requests
import w3lib.url

from page import Page


class Website:

    # (tag, link_attribute) tuples for retrieving assets.
    asset_tags = (('link', 'href'), ('script', 'src'), ('img', 'src'))
    # Max number of pages to crawl
    max_crawl = 20

    def __init__(self, seed):
        # Dictionary mapping of URL strings to Page objects.
        self.pages = dict()
        # We use canonical form of the seed URL so we can identify same
        # pages. ex. example.com/ is equal to example.com or
        # example.com/?key1=value1&key2=value2 equal to
        # example.com/?key2=value2&key1=value1
        seed = w3lib.url.canonicalize_url(seed)
        # We use ordered dict as a set. It is ordered so runs are consistent.
        self.to_visit = OrderedDict(((seed, None),))
        parse_seed = urlparse(seed)
        self.hostname = parse_seed.hostname

    def fix_relative_link(self, link, parsed_url):
        """
        Return absolute URL from relative link in a page.

        Fixes relative URLs like '/' for homepage etc.
        """
        parse_link = urlparse(link)
        link_hostname = parse_link.hostname
        if link_hostname is None:
            link_hostname = parsed_url.hostname
            link = urlunparse((
                parsed_url.scheme, parsed_url.netloc, link,
                None, None, None
            ))
        return link, link_hostname

    def fix_link(self, link, parsed_url):
        """Returns absolute and canonical URL from a relative one."""
        link = w3lib.url.canonicalize_url(link)
        link, link_hostname = self.fix_relative_link(link, parsed_url)
        return link, link_hostname

    def find_links(self, page, bs, parsed_url):
        """Finds links in the page, adds it to the page and to_visit set."""
        for link_tag in bs.find_all('a'):
            link = link_tag.get('href')
            if not link:
                continue
            # We add the link to page with no changes.
            page.links.add(link)
            link, link_hostname = self.fix_link(link, parsed_url)
            # Only follow this link if it hasn't been visited before and
            # it has the same hostname.
            if link not in self.pages and self.hostname == link_hostname:
                self.to_visit[link] = None

    def scrape_url(self, url):
        """Scrapes a single URL."""
        print("Scraping {}".format(url))
        page = Page(url)
        self.pages[url] = page
        response = requests.get(url)
        if response.status_code != requests.codes.ok:
            return
        # NOTE: html.parser engine is slower than lxml
        bs = BeautifulSoup(response.text, 'lxml')
        parsed_url = urlparse(url)
        # Find links.
        self.find_links(page, bs, parsed_url)
        # Find assets.
        for tag_name, attr in self.asset_tags:
            for tag in bs.find_all(tag_name):
                link = tag.get(attr)
                # script src might be empty if it is inlined.
                if link:
                    page.assets.add(link)

    def scrape(self):
        """
        Scrape starting from the seed URL that Website is initialized with.

        We gather all links and assets and we only follow URLs with the same
        hostname.
        """
        count = 0
        while self.to_visit:
            url, _ = self.to_visit.popitem()
            self.scrape_url(url)
            count += 1
            if count > self.max_crawl:
                break

    async def async_scrape_url(self, url):
        """Scrapes a single URL."""
        print("Scraping {}".format(url))
        page = Page(url)
        self.pages[url] = page
        # TODO: Better to use same session for all requests as it has
        # connection pooling and other improvements.
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != requests.codes.ok:
                    return
                # NOTE: html.parser engine is slower than lxml
                bs = BeautifulSoup(await response.text(), 'lxml')
                parsed_url = urlparse(url)
                # Find links.
                self.find_links(page, bs, parsed_url)
                # Find assets.
                for tag_name, attr in self.asset_tags:
                    for tag in bs.find_all(tag_name):
                        link = tag.get(attr)
                        # script src might be empty if it is inlined.
                        if link:
                            page.assets.add(link)

    def async_scrape(self):
        """
        Scrape starting from the seed URL that Website is initialized with.

        We gather all links and assets and we only follow URLs with the same
        hostname.
        """
        loop = asyncio.get_event_loop()
        count = 0
        while self.to_visit:
            print('There are {} links to visit.'.format(
                len(self.to_visit)))
            count += len(self.to_visit)
            coros = [
                self.async_scrape_url(url) for url, _ in
                self.to_visit.items()
            ]
            self.to_visit.clear()
            futures = asyncio.gather(*coros)
            loop.run_until_complete(futures)
            if count > self.max_crawl:
                break
        loop.close()

    def print_sitemap(self, async=False):
        """
        Scrapes a website starting with URL argument seed and prints sitemap.
        """
        if async:
            self.async_scrape()
        else:
            self.scrape()
        print('Sitemap:\n', self)

    def __str__(self):
        """
        String representation each page and their attributes (assets, links).
        """
        return '\n****\n'.join(str(page) for url, page in self.pages.items())


if __name__ == '__main__':
    fire.Fire(Website)
