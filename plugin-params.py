import argparse
import json
import re
import sys

#Replace tokens in a document with values from a JSON formatted config
class TokenReplacer:

    # Match ${aaa.bbb.ccc...} tokens, returning aaa.bbb.ccc... as match group 1
    __token_re = '\$\{([^\}]*)\}'

    def __init__(self, config):
        self.config = config
        self.all_good = True

    # Lookup hierarchical keys in config c, return value
    # throws KeyError if key not found
    # throws ValueError if terminal value is not a string
    def __lookup(self, c, lat):
        # If no more segments in key then this must be the terminal entry and so should be a string
        # Support replacement of embedded tokens in the terminal value by calling replace_tokens!
        if not lat:
            if not isinstance(c, str):
                raise ValueError
            return self.replace_tokens(c)
        
        # More segments so look up the next one...
        car = lat.pop(0)
        # c[car] throws a KeyError if car is not found
        return self.__lookup(c[car], lat)

    # Called for each match by re.sub(). Return corresponding config value for matched token.
    def __lookup_match(self, matchobj):
        try:
            return self.__lookup(self.config, matchobj.group(1).strip().split('.'))
        except (KeyError, ValueError) as e:
            self.all_good = False
            bad_token = '${' + matchobj.group(1) + '}'
            sys.stderr.write(
                f"Error: Token {bad_token} is not found in config\n" if isinstance(e, KeyError)
                        else f"Error: Token {bad_token} is not a terminal string in the config\n"
                        )
            return bad_token

    # Replace tokens with looked up values from config
    def replace_tokens(self, str):
        return re.sub(self.__token_re,
                        lambda matchobj: self.__lookup_match(matchobj),
                        str)

#Read in input file using passed in read_file_contents function that takes a TextIOWrapper variable
def read_file(file_name, read_file_contents):
    try:
        with open(file_name, 'r') as reader:
            try:
                return read_file_contents(reader)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Preprocess a text file and apply substitutions for all tokens.'
        ' Send updated text to sysout.')
    parser.add_argument('input', help='the input file')
    parser.add_argument('--config', help='the config file [app.json]',
        default='app.json')
    args = parser.parse_args()

    try:
        token_replacer = TokenReplacer(read_json_file(args.config))
        input_str = read_text_file(args.input)
    except Exception as e:
        sys.exit(f"Error during initialization: <${str(e)}>.")

    print(token_replacer.replace_tokens(input_str))

    #Exit with error if not all_good
    if not token_replacer.all_good:
        sys.exit("Error(s) detected.")
