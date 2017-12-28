import csv


class CsvReader:
    """
    A CSV reader which will read rows from CSV file "f",
    which is encoded in the given encoding.
    """
    reader = None

    def __init__(self, csv_file, mode='r', delimiter=';'):
        self.f = open(csv_file, mode, newline='\n', encoding='utf-8')
        self.reader = csv.reader(self.f, delimiter=delimiter, dialect=csv.excel)

    def readrows(self):
        return self.reader

    def close(self):
        self.f.close()
