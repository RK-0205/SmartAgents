import urllib.robotparser
from urllib.parse import urlparse

class RobotsTXTParser:

    def is_allowed(self, url, user='*'):
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        return rp.can_fetch(user, url)