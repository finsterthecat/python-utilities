#! /usr/local/bin/python3

import argparse
import re
import sys
import fileio
import fileinput

#Replace tokens found in input with values from a JSON formatted config
class TokenReplacer:

    # Match ${aaa.bbb.ccc...} tokens, returning aaa.bbb.ccc... as match group 1
    __token_re = '\$\{([^\}]*)\}'

    def __init__(self, config):
        self.config = config
        self.token_count = 0
        self.bad_token_count = 0

    # Lookup hierarchical keys in config c, return corresponding value
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
    # Count cases where the token is not found.
    # Client can check the count to determine whether all tokens found
    def __lookup_match(self, matchobj):
        self.token_count += 1
        try:
            return self.__lookup(self.config, matchobj.group(1).strip().split('.'))
        except (KeyError, ValueError) as e:
            self.bad_token_count += 1
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

    try:
        for line in fileinput.input(files=args.input, encoding="utf-8"):
            print(token_replacer.replace_tokens(line), end="")
    except Exception as e:
        sys.exit(f"{e.strerror}: {e.filename}")

    #Exit with error if errors detected by token_replacer
    if not token_replacer.is_all_good:
        sys.exit(f"{token_replacer.bad_token_count} token error" +
            ("s" if token_replacer.bad_token_count > 1 else "") )
