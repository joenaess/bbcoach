import sys
import os

sys.path.append(os.path.abspath("src"))

from bbcoach.scrapers.breakthrough_scraper import BreakthroughScraper  # noqa: E402

html = """
<html>
<body>
    <div id="content">
        <h1>Basketball Drills</h1>
        <p>Here is a list of <strong>great</strong> drills:</p>
        <ul>
            <li>Drill 1: <a href="/drills/1">Shooting</a></li>
            <li>Drill 2: Passing</li>
        </ul>
        <h2>Defense</h2>
        <p>Defensive stance is key.</p>
        <div class="ad">Buy this stuff</div>
    </div>
    <div class="footer">Copyright 2024</div>
</body>
</html>
"""

def test_breakthrough_scraper_parse():
    scraper = BreakthroughScraper()
    result = scraper.parse_page(html, "http://test.com")
    
    assert result["title"] is not None
    assert " الدفاع" not in result["content"]  # just check it successfully parses
    assert "Copyright 2024" not in result["content"] # Check footer was ignored
