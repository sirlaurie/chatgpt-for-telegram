#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung


__all__ = (
    "add",
    "update",
    "query",
    "query_one",
    "is_allowed",
)

from typing import Tuple

import tiktoken

# from .db import DBClient
from .checks import is_allowed, add, update, query, query_one
from src.constants import (
    linux_terminal_prompt,
    rewrite_prompt,
    cyber_secrity_prompt,
    etymologists_prompt,
    genius_prompt,
    expand_prompt,
    gpt_4_v,
    gpt_4_1106,
    gpt_3p5_turbo,
    gpt_3p5_turbo_0613,
    gpt_3p5_turbo_16k,
    gpt_3p5_turbo_16k_0613,
)

# client = DBClient()


def pick(act: str) -> str:
    """
    Function that matches the passed-in string to a known set of strings and returns the associated function.

    Args:
        act (str): The action string to match.

    Returns:
        str: default string.
    """
    match act:
        case "/linux_terminal":
            return linux_terminal_prompt
        case "/rewrite":
            return rewrite_prompt
        case "/cyber_secrity":
            return cyber_secrity_prompt
        case "/etymologists":
            return etymologists_prompt
        case "/genius":
            return genius_prompt
        case "/expand":
            return expand_prompt
        case _:
            return "who are you?"


token_price = {
    gpt_4_v: 0.03,
    gpt_4_1106: 0.03,
    gpt_3p5_turbo: 0.002,
    gpt_3p5_turbo_0613: 0.002,
    gpt_3p5_turbo_16k: 0.004,
    gpt_3p5_turbo_16k_0613: 0.004,
}


def usage_from_messages(message: str, model="gpt-3.5-turbo-0613") -> Tuple[int, str]:
    """Return the number of tokens used by a list of messages."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    num_tokens += len(encoding.encode(message))
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    price = f"{num_tokens / 1000 * token_price.get(model, 0.004):.5f}"
    return num_tokens, price
