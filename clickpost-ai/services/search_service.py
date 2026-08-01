import logging
import time

import requests

from config import TAVILY_API_KEY

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        self.api_key = TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"

    def search_company(self, company: str, website: str) -> str:
        query = (
            f'"{company}" {website} '
            '(funding OR hiring OR expansion OR "shipping complaints" '
            'OR "returns complaints" OR "technology stack" '
            'OR "Loop Returns" OR "AfterShip" OR "Redo" '
            'OR Trustpilot OR Reddit)'
        )

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": 3,
        }

        for attempt in range(3):
            try:
                if not self.api_key:
                    return ""

                response = requests.post(
                    self.base_url,
                    json=payload,
                    timeout=30,
                )

                response.raise_for_status()
                data = response.json()

                results = []

                for result in data.get("results", [])[:3]:
                    title = result.get("title", "")
                    url = result.get("url", "")
                    content = (result.get("content") or "")[:180]

                    results.append(
                        f"Title: {title}\n"
                        f"URL: {url}\n"
                        f"Snippet: {content}"
                    )

                return "\n\n".join(results)

            except Exception as e:
                logger.warning(
                    f"Tavily search attempt {attempt + 1} failed for {company}: {e}"
                )

                if attempt == 2:
                    logger.error(
                        f"Failed to search for {company} after 3 attempts."
                    )
                    return ""

                time.sleep(2)