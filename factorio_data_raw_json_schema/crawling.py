from typing import Any, cast

from bs4 import BeautifulSoup
import requests
import requests_cache
import requests_file  # type: ignore


# Work around non-pickeability of `requests_cache.CachedSession`
# Not great because we actually need only one instance per worker process and are creating one per task, i.e. one per download.
class _CachedSession:
    def __init__(self) -> None:
        self.session = requests_cache.CachedSession()

    def __getstate__(self) -> dict[str, Any]:
        return {}

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.session = requests_cache.CachedSession()

    def get(self, *args: Any, **kwargs: Any) -> requests.Response:
        return self.session.get(*args, **kwargs)


class Crawler:
    def __init__(self, root_url: str) -> None:
        if not root_url.endswith("/"):
            root_url += "/"
        self.root_url = root_url
        if root_url.startswith("file://"):
            self.session = requests.Session()
            self.session.mount("file://", requests_file.FileAdapter())
        else:
            self.session = cast(requests.Session, _CachedSession())

    def get(self, *path: str) -> BeautifulSoup:
        url = self.root_url + "/".join(path) + ".html"
        response = self.session.get(url)
        response.raise_for_status()
        response.encoding = "utf-8"
        # @todo Maybe use a SoupStrainer for faster parsing
        # (https://www.crummy.com/software/BeautifulSoup/bs4/doc/#parsing-only-part-of-a-document)
        # (py-spy shows that most time is spent in parsing)
        return BeautifulSoup(response.text, "lxml")
