import csv


class CsvWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """
    writer = None

    def __init__(self, csv_file, header, mode='w'):
        self.f = open(csv_file, mode, newline='\n', encoding='utf-8')
        self.writer = csv.DictWriter(self.f, delimiter=';', dialect=csv.excel, fieldnames=header)
        self.writer.writeheader()

    def writerow(self, row):
        self.writer.writerow(row)

    def writerows(self, rows):
        self.writer.writerows(rows)

    def close(self):
        self.f.close()
