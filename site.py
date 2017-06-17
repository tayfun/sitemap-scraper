from collections import deque


class Site:
    def __init__(self, seed):
        # Dictionary mapping of URL strings to Page objects.
        self.pages = dict()
        # Add seed URL to start scraping from.
        self.to_visit = deque([seed])
