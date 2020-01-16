import re
import string
import json
import datetime

color_pattern = re.compile("\\033\[\d+m")
separator = re.compile('=')
year = datetime.datetime.now().year

# Reference for string to avoid copying it
class Log:
    def __init__(self, log):
        self.log = log

    def __getitem__(self, key):
        return self.log[key]


def no_color(log):
    res = re.sub(color_pattern, '', log)
    return res


def is_diagnostic(log):
    return 'TRACE diagnostic' in log


def parse_obj(log, pos):
    key_s = pos
    while log[key_s - 1].isalnum():
        key_s -= 1
    key = log[key_s: pos]

    if log[pos + 1] == '"': # parse a string
        value_s = pos + 1
        value_e = pos + 2
        while log[value_e] != '"' or log[value_e - 1] == '\\':
            value_e += 1
        value = log[value_s: value_e + 1]

    elif log[pos + 1].isdigit(): # parse a number
        value_e = pos + 1
        while log[value_e].isdigit():
            value_e += 1
        value = int(log[pos + 1: value_e])
        value_e -= 1

    return ((key, value), value_e)


def parse_date(log):
    pos, blank = 0, 0
    while blank < 3:
        blank += int(log[pos] == ' ')
        pos += 1
    date = log[:pos - 1]
    res = datetime.datetime.strptime(date, "%b %d %H:%M:%S.%f")
    res = res.replace(year=year)
    return res


def parse(log):
    log = Log(log)

    result = {}
    last = 0

    for match in re.finditer(separator, log.log):
        s = match.start()
        if s <= last:
            continue

        ((key, value), last) = parse_obj(log, s)

        if isinstance(value, str):
            value = json.loads(value)

        try:
            if isinstance(value, str):
                # Try to parse inner string as json
                value = json.loads(value)
        except json.decoder.JSONDecodeError:
            pass

        result[key] = value


    result['date'] = parse_date(log)
    return fix_large_integer(result)


def parse_all(lines):
    return map(parse, filter(is_diagnostic, map(no_color, lines)))


# MongoDB don't accept numbers greater signed 64 bits integer (2**63 - 1).
# Convert such numbers into strings.
def fix_large_integer(value):
    if isinstance(value, datetime.datetime):
        return value

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
