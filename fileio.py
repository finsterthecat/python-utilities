#Read in input file using passed in read_file_contents function that takes a TextIOWrapper variable
import sys
import json
import csv

def read_file(file_name, file_content_reader):
    try:
        with open(file_name, 'r', encoding='utf-8-sig') as reader:
            try:
                return file_content_reader(reader)
            except Exception as e:
                sys.stderr.write(f"Error reading {file_name}: {e.args[0]}\n")
                raise e;
    except Exception as e:
        sys.stderr.write(f"Error opening {file_name}: {e.strerror}\n")
        raise e;

def read_json_file(file_name):
    return read_file(file_name, lambda reader: json.load(reader))

def read_text_file(file_name):
    return read_file(file_name, lambda reader: reader.read())

def read_csv_file(file_name):
    return read_file(file_name, lambda reader: list(csv.DictReader(reader)))

def just_give_me_the_reader(file_name):
    return read_file(file_name, lambda reader: reader)
