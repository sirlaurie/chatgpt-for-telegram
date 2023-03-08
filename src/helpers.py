
import unicodedata

escape_char = [
    '!',
    '<',
    '>',
    '_',
    '~',
    '`',
    '#',
    '-',
    '=',
    ]


def to_half_width(text: str) -> str:
    text = text.replace('\u3000', ' ').replace('，', ', ').replace('。', '. ')
    return unicodedata.normalize('NFKC', text)


def escape_extend(string: str) -> str:
    string = to_half_width(string).strip()
    # for char in escape_char:
    #   if (char in string) and {f'\\{char}' in string}:
    #     string = string
    #   if (char in string) and {f'\\{char}' not in string}:
    #     string = string.replace(char, f'\\{char}')
    #   else:
    #     string = string
    return f"```\n{string}\n```"

