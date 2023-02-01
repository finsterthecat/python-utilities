# Python Utilities

A collection of utilities written in Python

1. [plugin-params](#utility-plugin-params) will pre-process (a) text file(s) by plugging in values from a config file for tokens found in the text file(s). The tokens are delimited by ```${``` and ```}```. The value contained within the delimiters is a segmented string with segments separated by periods ```.```. The segmented string is used to traverse the json config to retrieve the configured value for each token. The processed text is sent to ```stdout```.

That's all for now. Stay tuned for more utilities!

## Utility: plugin-params

### Usage

```bash
usage: plugin-params.py [-h] [--config CONFIG] [input ...]

Preprocess a text file and apply substitutions for all tokens. Send updated text to stdout.

positional arguments:
  input            the input file(s), if empty, stdin is used

options:
  -h, --help       show this help message and exit
  --config CONFIG  the config file [app.json]
```

### JSON Config

The JSON Config file is a simple 'map of maps'. The included app.json file is intended to serve as an example that can be referenced when constructing your own config file:

```json
{
    "creature":
        {"name": "Fuzzy Wuzzy",
            "animal": "${global.mammaloftheday}",
            "defining_attribute": "no ${global.bodycover}",
            "assertion": "wasn't ${global.hair_characteristic}, was he?"
        },
    "global":
        {
            "title": "A ${creature.animal} Named ${creature.name}",
            "mammaloftheday": "bear",
            "bodycover": "${global.hairorfur}",
            "hairorfur": "hair",
            "hair_characteristic": "fuzzy"
        }
}
```

If your input file contains the line:

```text
${creature.name} was a ${creature.animal}
```

The corresponding output will be:

```text
Fuzzy Wuzzy was a bear
```

Notice that the processing supports recursive matching of tokens by looking up tokens in the matched strings.