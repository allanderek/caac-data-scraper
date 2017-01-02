import csv

import requests
from bs4 import BeautifulSoup

power_of_ten_fields = {
    0: 'event',
    1: 'time',
    5: 'position',
    9: 'venue',
    10: 'meeting',
    11: 'date',
    12: 'venue-link'
    }

class RaceResult(object):
    fields = power_of_ten_fields

    # This could all be made a bit simpler if we just accepted that each line
    # should contain the athlete information, and then not be bothered  by the
    # fact that we would be outputting that unnecessarily for every line in a
    # file dedicated to a single athlete.
    field_names = [power_of_ten_fields.get(i, "") for i in range(13)]
    extra_names = ['Athlete', 'Profile Link 1', 'Profile Link 2']

    def __init__(self, values=None):
        assert values is not None
        self.values = values

    @property
    def event(self):
        assert 'event' in self.field_names
        return self.values[self.field_names.index('event')]

    def show(self):
        for index, field in self.fields.items():
            print("{}: {}".format(field, self.values[index]))

    def csv_line(self, csvwriter):
        csvwriter.writerow(self.values)

    def generalise(self, athlete):
        """Changes the results line from one suitable for a CSV dedicated to a
        single athlete, to one suitable for a general results file. In other
        words put the athlete information into the results line."""
        extra_values = [athlete.full_name,
                        athlete.power_of_ten_link,
                        athlete.runbritain_link]
        self.field_names = self.extra_names + self.field_names
        self.values = extra_values + self.values


class Athlete(object):
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name
        self.club = "Corstorphine"
        self.power_of_ten_link = None
        self.runbritain_link = None

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

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
            values = [c.get_text() for c in cells]
            for index, cell in enumerate(cells):
                if power_of_ten_fields.get(index, "") == 'venue':
                    if cell.a:
                        relative_venue_link = cell.a.get('href')
                        # We could of course use urllib from the standard library
                        # to do this, and if it gets anymore complex then we should
                        # but for now this is simple enough.
                        venue_link = relative_venue_link.replace('../', 'http://powerof10.info/')
                    else:
                        venue_link = 'no venue link'
                    break
            else:
                venue_link = "no venue link"
            values.append(venue_link)
            return RaceResult(values=values)
        results = []
        for perf_table in perf_tables:
            these_results = (create_result(r) for r in perf_table.find_all('tr'))
            results.extend(r for r in these_results if r and r.event != 'Event')
        self.race_results = results

    def show_results(self):
        for r in self.race_results:
            r.show()

    def save_results_as_csv(self):
        filename = "results/" + self.first_name + '_' + self.last_name + ".csv"
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile,
                delimiter=',',
                quotechar='|',
                quoting=csv.QUOTE_MINIMAL
                )
            csvfile.write("# Profile link: {}\n".format(self.power_of_ten_link))
            csvfile.write("# Profile link: {}\n".format(self.runbritain_link))
            csvfile.write("#")
            csvwriter.writerow(RaceResult.field_names)
            for r in self.race_results:
                r.csv_line(csvwriter)

    def add_to_main_results(self, csvwriter):
        for r in self.race_results:
            r.generalise(self)
            r.csv_line(csvwriter)

if __name__ == "__main__":
    athletes = [
        Athlete("Christopher", "O'Brien"),
        Athlete("Steven", "O'Brien"),
        Athlete("Moray", "Anderson"),
        Athlete("Craig", "Knowles"),
        Athlete("Tom", "Hunt")
    ]
    for athlete in athletes:
        athlete.get_profile_links()
        athlete.get_race_results()
        athlete.save_results_as_csv()
    with open('results/all.csv', 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile,
                delimiter=',',
                quotechar='|',
                quoting=csv.QUOTE_MINIMAL
                )
            csvfile.write("#")
            csvwriter.writerow(RaceResult.extra_names + RaceResult.field_names)
            for athlete in athletes:
                athlete.add_to_main_results(csvwriter)