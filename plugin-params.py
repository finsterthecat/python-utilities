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
        self.missing_tokens = set()
        self.line_num = 0

    # Called for each match by re.sub(). Return corresponding config value for matched token.
    # Count cases where the token is not found.
    # Client can check the count to determine whether all tokens found
    def __lookup_match(self, matchobj):

        # Apply the named transform to string c.
        # Throw AttributeError if unrecognized transform
        def xform(c, xform_func):
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
        def lookup(c, lat, xform_func):
            # If no more segments in key then this must be the terminal entry and so should be a string
            # Support replacement of embedded tokens in the terminal value by calling replace_tokens!
            if not lat:
                if not isinstance(c, str):
                    raise ValueError(f"Key does not equate to a string in the config")
                return xform(self.__replace_tokens(c), xform_func)
            
            # More segments so look up the next one...
            car = lat.pop(0)
            # c[car] throws a KeyError if car is not found
            try:
                return lookup(c[car], lat, xform_func)
            except KeyError as e:
                raise KeyError("Key is not found in config")

        self.token_count += 1
        try:
            lookup_lat = matchobj.group(1).strip().split('.')
            xform_func = matchobj.group(3) if len(matchobj.groups()) > 2 else None
            return lookup(self.config, lookup_lat, xform_func)
        except (KeyError, ValueError, AttributeError) as e:
            token = matchobj.group(0)
            self.missing_tokens.add(token)
            sys.stderr.write(f"Error on line {self.line_num}: Bad token \"{token}\". {e.args[0]}\n")
            # Keep the token asis if error(s) detected
            return token

    # Replace tokens with looked up values from config
    def __replace_tokens(self, str):
        return re.sub(self.__TOKEN_RE,
                        lambda matchobj: self.__lookup_match(matchobj),
                        str)
    
    # Replace tokens in a string with looked up values from config
    def process_line(self, str):
        self.line_num += 1
        try:
            return self.__replace_tokens(str)
        except Exception as e:
            sys.exit(f"{e.strerror}: {e.filename}")

    # Process all lines for all files, outputting the results using lambda output_func, default prints to stdout
    def process_files(self, files, output_func = lambda line: print(line, end="")):
        for line in fileinput.input(files=files, encoding="utf-8"):
            output_func(self.process_line(line))

    # Have all the tokens encountered been valid?
    def is_all_good(self):
        return not self.missing_tokens

    # Reset the bad token count to zero
    def reset(self):
        self.missing_tokens = set()

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
        sys.stderr.write(f"Error: {len(token_replacer.missing_tokens)} missing token" +
            ("s" if len(token_replacer.missing_tokens) > 1 else "") + " found in input and/or config:\n")
        for token in token_replacer.missing_tokens:
            sys.stderr.write((f"\t{token}\n"))
        sys.exit("Bad tokens found in input")
