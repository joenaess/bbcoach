import requests
from bs4 import BeautifulSoup, NavigableString, Tag, Comment
import logging
import re
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class BreakthroughScraper:
    BASE_URL = "https://www.breakthroughbasketball.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def fetch_page(self, url):
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def clean_soup(self, soup):
        """Removes unwanted elements like nav, footer, scripts, ads."""
        for element in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            element.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove specific classes or ids known to be non-content
        # Based on initial inspection, sidebars and ads usually have specific classes
        for selector in [
            ".sidebar",
            ".ad",
            ".social-share",
            ".comment-section",
            "#header",
            "#footer",
            ".topbanner1",
            ".drillslinks",
            ".supernav",
            ".logobar",
            ".menubar",
            ".footer",
            ".subfooter",
            ".exitintentpopupoverlay",
        ]:
            for element in soup.select(selector):
                element.decompose()

        return soup

    def get_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(base_url, href)
            # Filter for relevant links (drills, plays)
            if "/drills/" in full_url or "/plays/" in full_url:
                links.add(full_url)
        return list(links)

    def element_to_markdown(self, element):
        """Recursively converts a BeautifulSoup element to Markdown."""
        if element is None:
            return ""

        if isinstance(element, NavigableString):
            text = element.strip()
            return text if text else ""

        if isinstance(element, Tag):
            content = ""
            for child in element.children:
                content += self.element_to_markdown(child)
                # Add space between inline elements if needed, but be careful not to break words
                if isinstance(child, Tag) and child.name in [
                    "a",
                    "strong",
                    "em",
                    "span",
                    "code",
                ]:
                    content += " "

            # Clean up double spaces from the loop above
            content = re.sub(r"\s+", " ", content).strip()

            if element.name == "h1":
                return f"\n# {content}\n\n"
            elif element.name == "h2":
                return f"\n## {content}\n\n"
            elif element.name == "h3":
                return f"\n### {content}\n\n"
            elif element.name == "h4":
                return f"\n#### {content}\n\n"
            elif element.name in ["p", "div", "section"]:
                # Only add newlines if there is content
                return f"{content}\n\n" if content else ""
            elif element.name == "ul":
                return f"{content}\n"
            elif element.name == "ol":
                return f"{content}\n"
            elif element.name == "li":
                # Determine if parent is ol or ul matching is hard in recursion without context,
                # but standard markdown readers handle - for list items well.
                return f"- {content}\n"
            elif element.name == "a":
                href = element.get("href", "")
                if href and content:
                    return f"[{content}]({href})"
                return content
            elif element.name in ["strong", "b"]:
                return f"**{content}**"
            elif element.name in ["em", "i"]:
                return f"*{content}*"
            elif element.name == "code":
                return f"`{content}`"
            elif element.name == "pre":
                return f"```\n{content}\n```\n\n"
            elif element.name == "blockquote":
                return f"> {content}\n\n"
            elif element.name == "br":
                return "\n"
            elif element.name == "img":
                alt = element.get("alt", "")
                src = element.get("src", "")
                if src:
                    return f"![{alt}]({src})\n"
                return ""
            else:
                return f"{content} "

        return ""

    def parse_page(self, html, url):
        soup = BeautifulSoup(html, "html.parser")
        soup = self.clean_soup(soup)

        title = "No Title"
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Helper to find the best candidate for content
        # Priority:
        # 1. specific layout containers (e.g. .drillscontainer)
        # 2. #content or .contentwrapper
        # 3. body (fallback)

        candidates = [
            soup.find(class_="drillscontainer"),
            soup.find(id="content"),
            soup.find(class_="contentwrapper"),
            soup.find(class_="middle-column"),  # Common in older layouts
        ]

        main_content = None
        for candidate in candidates:
            if candidate:
                # Basic check to ensure it has some text length
                if len(candidate.get_text(strip=True)) > 200:
                    main_content = candidate
                    break

        if not main_content:
            main_content = soup.body

        markdown_content = self.element_to_markdown(main_content)

        # Clean up excessive newlines
        markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

        return {"title": title, "url": url, "content": markdown_content}

    def scrape_resource(self, url):
        """Scrapes a single resource page."""
        html = self.fetch_page(url)
        if not html:
            return None

        return self.parse_page(html, url)
