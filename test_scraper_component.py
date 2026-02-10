from bbcoach.scrapers.breakthrough_scraper import BreakthroughScraper

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

scraper = BreakthroughScraper()
result = scraper.parse_page(html, "http://test.com")
print(f"Title: {result['title']}")
print("--- Content ---")
print(result["content"])
