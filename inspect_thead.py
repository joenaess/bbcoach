from bs4 import BeautifulSoup


def inspect_thead():
    with open("page_dump_genius.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if not table:
        print("No table found")
        return

    thead = table.find("thead")
    if thead:
        rows = thead.find_all("tr")
        print(f"Number of rows in thead: {len(rows)}")
        for i, tr in enumerate(rows):
            headers = [th.get_text(strip=True) for th in tr.find_all("th")]
            print(f"Row {i} headers ({len(headers)}): {headers}")
    else:
        print("No thead found")


if __name__ == "__main__":
    inspect_thead()
