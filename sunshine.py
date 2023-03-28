#! /usr/local/bin/python3

import argparse
import re
import sys
import fileio
import csv

parser = argparse.ArgumentParser(
    description='Find all sunshine list employees whose job title matches filtered key words.'
    ' Send matched records to stdout, which you can redirect to a file.')
parser.add_argument('input', help='the sunshine csv file')
parser.add_argument("--filter", nargs="*", type=str, default=[], help='list of keywords to match in Job Title column')
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
