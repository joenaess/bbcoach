from bs4 import BeautifulSoup


def inspect_html():
    with open("page_dump_genius.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Find the table
    table = soup.find("table")
    if not table:
        print("No table found")
        return

    # Get headers
    headers = []
    thead = table.find("thead")
    if thead:
        headers = [th.get_text(strip=True) for th in thead.find_all("th")]

    print(f"Headers ({len(headers)}):")
    print(headers)

    # Get first few rows
    rows = []
    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr")[:5]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            rows.append(cells)

    print("\nFirst 5 Rows:")
    for row in rows:
        print(row)

    # Find Ali Sow specifically
    print("\nSearching for Ali Sow:")
    if tbody:
        for tr in tbody.find_all("tr"):
            if "Ali Sow" in tr.get_text():
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                print(cells)


if __name__ == "__main__":
    inspect_html()
