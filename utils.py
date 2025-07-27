import csv
import sys


def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def load_csv_rows(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))
