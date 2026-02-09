
import requests
from bs4 import BeautifulSoup

def test_scrape():
    url = "https://www.proballers.com/basketball/league/190/sweden-basketligan"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.text
        print(f"Successfully scraped: {title}")
        # Try to find a team or player link to confirm data access
        links = soup.find_all('a', href=True)
        print(f"Found {len(links)} links.")
        return True
    except Exception as e:
        print(f"Failed to scrape: {e}")
        return False

if __name__ == "__main__":
    test_scrape()
