class Page:
    def __init__(self, url):
        # URL is basically the ID of the page.
        self.url = url
        # Set of URL strings linked from this page.
        self.links = set()
        # Set of asset URL strings in this page.
        self.assets = set()
