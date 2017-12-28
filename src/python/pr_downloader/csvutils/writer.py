import csv


class CsvWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """
    writer = None

    def __init__(self, csv_file, mode='w'):
        self.f = open(csv_file, mode, newline='\n', encoding='utf-8')
        self.writer = csv.writer(self.f, delimiter=';', dialect=csv.excel)

    def writerow(self, row):
        self.writer.writerow(row)

    def writerows(self, rows):
        for row in rows:
            self.writer.writerow(row)

    def close(self):
        self.f.close()
