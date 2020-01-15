import re
import string
import json

color_pattern = re.compile("\\033\[\d+m")
separator = re.compile('="')


def no_color(log):
    res = re.sub(color_pattern, '', log)
    return res


def is_diagnostic(log):
    return 'TRACE diagnostic:' in log


def parse(log):
    result = {}

    for match in re.finditer(separator, log):
        s = match.start()
        key_s = s
        while log[key_s - 1].isalnum():
            key_s -= 1
        key = log[key_s:s]
        value_s = s + 1
        value_e = s + 2
        while log[value_e] != '"' or log[value_e - 1] == '\\':
            value_e += 1
        value = log[value_s:value_e + 1]
        result[key] = json.loads(value)

    return result


def parse_all(lines):
    return map(parse, filter(is_diagnostic, map(no_color, lines)))
