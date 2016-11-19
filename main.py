import csv

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
    
    def csv_line(self, csvwriter):
        csvwriter.writerow([getattr(self,f) for f in self.fields])


class Athlete(object):
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name
        self.club = "Corstorphine"
        self.power_of_ten_link = None
        self.runbritain_link = None

    def get_profile_links(self):
        url = "http://powerof10.info/athletes/athleteslookup.aspx"
        params = {'surname': self.last_name,
                  'firstname': self.first_name,
                  'club': "Corstorphine" }
        response = requests.post(url, params=params)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results_table = soup.find(id="cphBody_pnlResults")
        links = results_table.find_all('a')
        if len(links) > 0:
            local_url = links[0]['href']
            self.power_of_ten_link = "http://powerof10.info/athletes/" + local_url
            if len(links) > 1:
                self.runbritain_link = links[1]['href']

    def get_race_results(self):
        response = requests.get(self.power_of_ten_link)
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
        self.race_results = results

    def show_results(self):
        for r in self.race_results:
            r.show()
    
    def save_results_as_csv(self):
        filename = self.first_name + '_' + self.last_name + ".csv"
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile,
                
                delimiter=',', 
                quotechar='|', 
                quoting=csv.QUOTE_MINIMAL
                )
            csvfile.write("#")
            csvwriter.writerow(RaceResult.fields)
            for r in self.race_results:
                r.csv_line(csvwriter)

if __name__ == "__main__":
    athletes = [
        Athlete("Christopher", "O'Brien"),
        Athlete("Steven", "O'Brien"),
        Athlete("Moray", "Anderson")
    ]
    for athlete in athletes:
        athlete.get_profile_links()
        athlete.get_race_results()
        athlete.save_results_as_csv()
