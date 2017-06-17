from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup
import fire
import requests
import w3lib.url

from page import Page


class Site:

    # (tag, link_attribute) tuples for retrieving assets.
    asset_tags = (('link', 'href'), ('script', 'src'), ('img', 'src'))

    def __init__(self, seed):
        # Dictionary mapping of URL strings to Page objects.
        self.pages = dict()
        # Add seed URL to start scraping from. URLs in to_visit are always
        # normalized. We use canonical form of the URL so we can identify same
        # pages. ex. example.com/ is equal to example.com or
        # example.com/?key1=value1&key2=value2 equal to
        # example.com/?key2=value2&key1=value1
        self.to_visit = set([w3lib.url.canonicalize_url(seed)])
        parse_seed = urlparse(seed)
        self.hostname = parse_seed.hostname

    def scrape(self):
        """
        Start scraping from the seed URL that Site is initialized with.

        We gather all links and assets and we only follow URLs with the same
        hostname.
        """
        while self.to_visit:
            url = self.to_visit.pop()
            print("Visiting {}".format(url))
            page = Page(url)
            self.pages[url] = page
            response = requests.get(url)
            if response.status_code != requests.codes.ok:
                continue
            url_parse = urlparse(url)
            # NOTE: html.parser engine is slower than lxml
            bs = BeautifulSoup(response.text, 'html.parser')
            # Find links.
            for link_tag in bs.find_all('a'):
                link = link_tag.get('href')
                # We add the link as it is in the page (relative etc.)
                page.links.add(link)
                # We canonicalize the link to add back to the `to_visit` set.
                link = w3lib.url.canonicalize_url(link)
                parse_link = urlparse(link)
                link_hostname = parse_link.hostname
                # Fix relative URLs, like '/' for homepage etc.
                if link_hostname is None:
                    link_hostname = url_parse.hostname
                    link_params = (
                        url_parse.scheme, url_parse.netloc, link,
                        None, None, None
                    )
                    link = urlunparse(link_params)
                # Only follow this link if it hasn't been visited before and
                # it has the same hostname.
                if link not in self.pages and self.hostname == link_hostname:
                    self.to_visit.add(link)
            # Find assets.
            for tag_name, attr in self.asset_tags:
                for tag in bs.find_all(tag_name):
                    link = tag.get(attr)
                    # script src might be empty if it is inlined.
                    if link:
                        page.assets.add(link)

    def print_sitemap(self):
        """
        Scrapes a website starting with URL argument seed and prints sitemap.
        """
        self.scrape()
        print('Sitemap:\n', self)

    def __str__(self):
        """
        String representation each page and their attributes (assets, links).
        """
        return '\n****\n'.join(str(page) for url, page in self.pages.items())


if __name__ == '__main__':
    fire.Fire(Site)
