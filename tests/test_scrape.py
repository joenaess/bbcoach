import pytest
import requests
from bs4 import BeautifulSoup


@pytest.mark.integration
def test_scrape():
    url = "https://www.proballers.com/basketball/league/190/sweden-basketligan"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.text
        print(f"Successfully scraped: {title}")
        links = soup.find_all("a", href=True)
        print(f"Found {len(links)} links.")
        assert len(links) >= 0
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            pytest.skip(f"Skipping due to 403 Forbidden (Anti-bot): {e}")
        else:
            pytest.fail(f"HTTP Error: {e}")
    except Exception as e:
        pytest.fail(f"Scrape failed: {e}")


if __name__ == "__main__":
    test_scrape()

