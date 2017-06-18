from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup
import fire
import requests
import w3lib.url

from page import Page


class Website:

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
                self.to_visit.add(link)

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
            url = self.to_visit.pop()
            self.scrape_url(url)
            count += 1
            if count > 20:
                break

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
    fire.Fire(Website)
