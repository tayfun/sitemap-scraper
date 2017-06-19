# What is it?

This project scrapes a given domain and creates an internal site map of the
page with all the pages, links and assets they have. It prints this data in a
basic format.

There are two versions, first one runs sequentially and the second version
makes use of asyncio and aiohttp to run async so the program finishes faster
with a concurrent run. Note that this is still run in a single thread, but IO
blocking is avoided with concurrency.

# Install

    pyenv install 3.6.1
    pyenv shell 3.6.1
    mkvirtualenv sitemap-scraper && mkdir sitemap-scraper && cd sitemap-scraper
    git clone git@github.com:tayfun/sitemap-scraper.git
    pip install -r requirements.txt

# Usage

    python website.py --seed http://blog.tayfunsen.com/ print-sitemap

Or if you want to run async:

    python website.py --seed https://oneplus.net/uk/launch print-sitemap async

# Run tests

    pip install -r requirements_test.txt
    py.test tests.py
