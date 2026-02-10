from bs4 import BeautifulSoup


def inspect_first_cell():
    with open("page_dump_genius.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Find the table
    table = soup.find("table")
    if not table:
        print("No table found")
        return

    # Find Ali Sow specifically
    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            if "Ali Sow" in tr.get_text():
                first_cell = tr.find("td")
                print("First cell text:", first_cell.get_text(strip=True))
                print("First cell HTML:", first_cell.prettify())

                # Check for any other columns that might look like Team
                all_cells = tr.find_all("td")
                for i, cell in enumerate(all_cells):
                    print(f"Cell {i}: {cell.get_text(strip=True)}")


if __name__ == "__main__":
    inspect_first_cell()
