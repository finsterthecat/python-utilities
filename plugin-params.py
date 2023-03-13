#! /usr/local/bin/python3

import argparse
import re
import sys
import fileio
import fileinput

#Replace tokens found in input with values from a JSON formatted config
class TokenReplacer:

    # Match ${aaa.bbb.ccc...} tokens, returning aaa.bbb.ccc... as match group 1
    # Also matches an optional transform function appended to the token as match group 3
    __TOKEN_RE = '\$\{([^\}]*)\}(\.([a-z]+))?'

    def __init__(self, config):
        self.config = config
        self.token_count = 0
        self.bad_token_count = 0
        self.line_num = 0

    def __xform(self, c, xform_func):
        funcs = {
            None: lambda c: c,
            'capitalize': lambda c: c.capitalize(),
            'title': lambda c: c.title(),
            'upper': lambda c: c.upper(),
            'lower': lambda c: c.lower()
        }
        try:
            return funcs[xform_func](c);
        except KeyError as e:
            raise AttributeError(f"Unrecognized transformation function: {xform_func}")
    
    # Lookup hierarchical keys in config c, return corresponding value
    # throws KeyError if key not found
    # throws ValueError if terminal value is not a string
    # throws AttributeError if xform_func, if present, is not found
    def __lookup(self, c, lat, xform_func):
        # If no more segments in key then this must be the terminal entry and so should be a string
        # Support replacement of embedded tokens in the terminal value by calling replace_tokens!
        if not lat:
            if not isinstance(c, str):
                raise ValueError(f"Key does not equate to a string in the config")
            return self.__xform(self.__replace_tokens(c), xform_func)
        
        # More segments so look up the next one...
        car = lat.pop(0)
        # c[car] throws a KeyError if car is not found
        try:
            return self.__lookup(c[car], lat, xform_func)
        except KeyError as e:
            raise KeyError("Key is not found in config")

    # Called for each match by re.sub(). Return corresponding config value for matched token.
    # Count cases where the token is not found.
    # Client can check the count to determine whether all tokens found
    def __lookup_match(self, matchobj):
        self.token_count += 1
        try:
            lookup_lat = matchobj.group(1).strip().split('.')
            xform_func = matchobj.group(3) if len(matchobj.groups()) > 2 else None
            return self.__lookup(self.config, lookup_lat, xform_func)
        except (KeyError, ValueError, AttributeError) as e:
            self.bad_token_count += 1
            sys.stderr.write(f"Error on line {self.line_num}: Bad token \"{matchobj.group(0)}\". {e.args[0]}\n")
            # Keep the token asis if error(s) detected
            return matchobj.group(0)

    # Replace tokens with looked up values from config
    def __replace_tokens(self, str):
        return re.sub(self.__TOKEN_RE,
                        lambda matchobj: self.__lookup_match(matchobj),
                        str)

    def process_line(self, str):
        self.line_num += 1
        return self.__replace_tokens(str)

    # Process all lines for all files, outputting the results using lambda output_func, default prints to stdout
    def process_files(self, files, output_func = lambda line: print(line, end="")):
        try:
            for line in fileinput.input(files=files, encoding="utf-8"):
                output_func(self.process_line(line))
        except Exception as e:
            sys.exit(f"{e.strerror}: {e.filename}")

    # Have all the tokens encountered been valid?
    def is_all_good(self):
        return self.bad_token_count == 0

    # Reset the bad token count to zero
    def reset(self):
        self.bad_token_count = 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Preprocess a text file and apply substitutions for all tokens.'
        ' Send updated text to stdout.')
    parser.add_argument('input', help='the input file(s), if empty, stdin is used', nargs='*')
    parser.add_argument('--config', help='the config file [app.json]',
        default='app.json')
    args = parser.parse_args()

    try:
        token_replacer = TokenReplacer(fileio.read_json_file(args.config))
    except Exception as e:
        sys.exit(f"Error during initialization: <${str(e)}>.")

    token_replacer.process_files(args.input)

    #Exit with error if errors detected by token_replacer
    if not token_replacer.is_all_good():
        sys.exit(f"Error: {token_replacer.bad_token_count} token error" +
            ("s" if token_replacer.bad_token_count > 1 else "") + " found in input and/or config")
