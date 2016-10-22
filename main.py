import requests
from bs4 import BeautifulSoup

class RaceResult(object):
    fields = ['event', 'time', 'position', 'venue', 'meeting', 'date']
    
    def __init__(self, **kwargs):
        assert all(f in kwargs for f in self.fields)
        assert all(f in self.fields for f in kwargs)
        for f in self.fields:
            setattr(self, f, kwargs[f])
    
    def show(self):
        for f in self.fields:
            print("{}: {}".format(f.upper(), getattr(self, f)))

def scrape_data():
    response = requests.get('http://powerof10.info/athletes/profile.aspx?athleteid=4392')
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    def results_table(table):
        try:
            
            table_cells = table.find_all('td')
            return table_cells[1].b.text == 'Event' and table_cells[2].b.text == 'Perf'
        except (ValueError, AttributeError, IndexError):
            return False
    perf_tables = [t for t in tables if results_table(t)]

    def create_result(row):
        cells = row.find_all('td')
        if len(cells) < 12:
            return None
        return RaceResult(
            event=cells[0].get_text(),
            time=cells[1].get_text(),
            position=cells[5].get_text(),
            venue=cells[9].get_text(),
            meeting=cells[10].get_text(),
            date=cells[11].get_text()
            )
    results = []
    for perf_table in perf_tables:
        these_results = (create_result(r) for r in perf_table.find_all('tr'))
        results.extend(r for r in these_results if r and r.event != 'Event')
    for r in results:
        r.show()

if __name__ == "__main__":
    scrape_data()