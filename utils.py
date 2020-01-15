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
        value = json.loads(value)

        try:
            # Try to parse inner string as json
            value = json.loads(value)
            value = fix_large_integer(value)
        except json.decoder.JSONDecodeError:
            pass

        result[key] = value

    return result


def parse_all(lines):
    return map(parse, filter(is_diagnostic, map(no_color, lines)))


# MongoDB don't accept numbers greater signed 64 bits integer (2**63 - 1).
# Convert such numbers into strings.
def fix_large_integer(value):
    if isinstance(value, int):
        if value >= 2**63:
            value = str(value)
        return value

    if isinstance(value, str):
        # Try to convert to int
        try:
            value = int(value)
            if value >= 2**63:
                value = str(value)
        except ValueError:
            pass

        return value

    if isinstance(value, dict):
        new_dic = {}
        for key, value in value.items():
            if key == '_id':
                continue
            new_dic[key] = fix_large_integer(value)
        return new_dic

    if isinstance(value, list):
        new_list = [fix_large_integer(x) for x in value]
        return new_list

    if value is None:
        return value

    assert False, f"{str(value)} | {type(value)}"
