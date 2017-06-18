from collections import OrderedDict
from unittest.mock import Mock

from bs4 import BeautifulSoup
import pytest

from page import Page
from website import Website


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture
def page_content():
    example_content = (
        '<html><body><a href="/"/><p>'
        '<a href="http://different_hostname">'
        '</a></p><a href="https://hostname"></a><p><p><a href="/new-url">'
        '</a></p></p></body>'
    )
    return example_content


def test_init_seed_is_canonical_slash_in_the_end():
    website = Website('http://blog.tayfunsen.com')
    # Slash is added to the end.
    assert website.to_visit == OrderedDict(
        (('http://blog.tayfunsen.com/', None),)
    )


def test_init_seed_is_canonical_get_parameter_order():
    website1 = Website('http://blog.tayfunsen.com/?key1=value1&key2=value2')
    website2 = Website('http://blog.tayfunsen.com/?key2=value2&key1=value1')
    assert website1.to_visit == website2.to_visit


@pytest.mark.parametrize('link, hostname, scheme, result', [
    ('/', 'hostname', 'http', 'http://hostname/'),
    ('/favico.ico', 'hostname', 'http', 'http://hostname/favico.ico'),
    ('/images/i.jpg', 'hostname', 'https', 'https://hostname/images/i.jpg'),
])
def test_fix_relative_link(link, hostname, scheme, result):
    mock_parsed_url = Mock()
    mock_parsed_url.hostname = hostname
    mock_parsed_url.scheme = scheme
    mock_parsed_url.netloc = hostname
    website = Website('seed_url')
    assert website.fix_relative_link(link, mock_parsed_url) == (
        result, hostname
    )


@pytest.mark.parametrize('link, hostname, scheme, result', [
    ('/', 'hostname', 'http', 'http://hostname/'),
    ('/favico.ico', 'hostname', 'http', 'http://hostname/favico.ico'),
    ('/images/i.jpg', 'hostname', 'https', 'https://hostname/images/i.jpg'),
    ('/?k1=v1&k2=v2', 'hostname', 'http', 'http://hostname/?k1=v1&k2=v2'),
    ('/?k2=v2&k1=v1', 'hostname', 'http', 'http://hostname/?k1=v1&k2=v2'),
])
def test_fix_link(link, hostname, scheme, result):
    mock_parsed_url = Mock()
    mock_parsed_url.hostname = hostname
    mock_parsed_url.scheme = scheme
    mock_parsed_url.netloc = hostname
    website = Website('seed_url')
    assert website.fix_link(link, mock_parsed_url) == (
        result, hostname
    )


@pytest.mark.parametrize('hostname, scheme, links, to_visit', [
    (
        'hostname',
        'http',
        {'/', '/new-url', 'http://different_hostname', 'https://hostname'},
        ('http://hostname/', 'https://hostname/', 'http://hostname/new-url')
    ),
])
def test_find_links(page_content, hostname, scheme, links, to_visit):
    mock_parsed_url = Mock()
    mock_parsed_url.hostname = hostname
    mock_parsed_url.scheme = scheme
    mock_parsed_url.netloc = hostname
    website = Website('http://hostname/url')
    # Simulate visiting the page.
    website.to_visit.popitem()
    page = Page('a_url')
    bs = BeautifulSoup(page_content, 'html.parser')
    website.find_links(page, bs, mock_parsed_url)
    assert page.links == links
    assert website.to_visit == OrderedDict((key, None) for key in to_visit)


@pytest.mark.parametrize('links, to_visit', [
    (
        {'/', '/new-url', 'http://different_hostname', 'https://hostname'},
        ('http://hostname/', 'https://hostname/', 'http://hostname/new-url')
    ),
])
def test_scrape_url(monkeypatch, page_content, links, to_visit):
    mock_response = Mock()
    mock_response.text = page_content
    mock_response.status_code = 200
    monkeypatch.setattr('website.requests.get', lambda x: mock_response)
    website = Website('http://hostname/url')
    # Simulate visiting the page.
    url, _ = website.to_visit.popitem()
    website.scrape_url(url)
    assert website.to_visit == OrderedDict((key, None) for key in to_visit)
    assert website.pages[url].links == links


@pytest.mark.parametrize('links, to_visit', [
    (
        {'/', '/new-url', 'http://different_hostname', 'https://hostname'},
        ('http://hostname/', 'https://hostname/', 'http://hostname/new-url')
    ),
])
def test_scrape(monkeypatch, page_content, links, to_visit):
    mock_response = Mock()
    mock_response.text = page_content
    mock_response.status_code = 200
    monkeypatch.setattr('website.requests.get', lambda x: mock_response)
    website = Website('http://hostname/url')
    website.scrape()
    # pages are 'http://hostname/url', 'http://hostname/new-url',
    # 'https://hostname/', 'http://hostname/', 'https://hostname/new-url'
    assert len(website.pages) == 5
