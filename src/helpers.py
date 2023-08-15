from typing import Tuple
import unicodedata
import tiktoken
from constants.models import (
    gpt_4,
    gpt_4_0314,
    gpt_4_0613,
    gpt_3p5_turbo,
    gpt_3p5_turbo_0613,
    gpt_3p5_turbo_16k,
    gpt_3p5_turbo_16k_0613
    )

escape_char = [
    "!",
    "<",
    ">",
    "_",
    "~",
    "`",
    "#",
    "-",
    "=",
]

token_price = {
    gpt_4: 0.03,
    gpt_4_0314: 0.03,
    gpt_4_0613: 0.03,
    gpt_3p5_turbo: 0.0015,
    gpt_3p5_turbo_0613: 0.0015,
    gpt_3p5_turbo_16k: 0.003,
    gpt_3p5_turbo_16k_0613: 0.003,
}


def to_half_width(text: str) -> str:
    text = text.replace("\u3000", " ").replace("，", ", ").replace("。", ". ")
    return unicodedata.normalize("NFKC", text)


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


def usage_from_messages(message: str, model="gpt-3.5-turbo-0613") -> Tuple[int, str]:
    """Return the number of tokens used by a list of messages."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    num_tokens += len(encoding.encode(message))
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    # price = num_tokens / 1000 * token_price.get(model, 0.003)
    price = "{:9f}".format(num_tokens / 1000 * token_price.get(model, 0.003))
    return num_tokens, price
