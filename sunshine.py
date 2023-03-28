#! /usr/local/bin/python3

import argparse
import re
import sys
import fileio
import csv

parser = argparse.ArgumentParser(
    description='Preprocess a text file and apply substitutions for all tokens.'
    ' Send updated text to stdout.')
parser.add_argument('input', help='the input file(s), if empty, stdin is used')
parser.add_argument("--filter", nargs="*", type=str, default=[])
args = parser.parse_args()

rows = fileio.read_csv_file(args.input)

ALL = "(Equity)|(Diversity)|(Inclusion)|(Anti-Racism)|(Indigenous)|(Equality)|(Rights)|(Gender)"

if args.filter == []:
    filter = ALL
else:
    filter = "(" + ")|(".join(args.filter) + ")"

sys.stderr.write(f"file is {args.input}. Filter: {filter}\n")

csv_columns = "Sector,Last Name,First Name,Salary,Benefits,Employer,Job Title,Year".split(",")

writer = csv.DictWriter(sys.stdout, fieldnames=csv_columns)

writer.writeheader()

count = 0
total = 0.0
for row in rows:
    if re.search(filter, row['Job Title'], re.I):
        count += 1
        total += float(row["Salary"])
        writer.writerow(row)

sys.stderr.write(f"{count} matches. Total is {total:9,.2f}. Average {(total/count):9,.2f}\n")
