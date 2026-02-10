from bs4 import BeautifulSoup


def inspect_all_tables():
    with open("page_dump_genius.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    print(f"Found {len(tables)} tables.")

    for i, table in enumerate(tables):
        thead = table.find("thead")
        headers = []
        if thead:
            rows = thead.find_all("tr")
            for tr in rows:
                headers.extend([th.get_text(strip=True) for th in tr.find_all("th")])
        print(f"Table {i} Headers ({len(headers)}): {headers}")


if __name__ == "__main__":
    inspect_all_tables()
