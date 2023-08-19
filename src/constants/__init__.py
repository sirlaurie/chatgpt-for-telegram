#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: loricheung

__all__ = (
    # commands
    "cyber_secrity_command",
    "etymologists_command",
    "genius_command",
    "linux_terminal_command",
    "model_switch_command",
    "reset_command",
    "rewrite_command",
    "translator_command",
    # messages
    "NOT_PERMITED",
    "NOT_ALLOWD",
    "YES_OR_NO_KEYBOARD",
    "TARGET_LANGUAGE_KEYBOARD",
    "ASK_FOR_PERMITED",
    "PROCESS_TIMEOUT",
    "APPROVED_MESSAGE",
    "DECLINE_MESSAGE",
    "WELCOME_MESSAGE",
    "NEW_CONVERSATION_MESSAGE",
    "INIT_REPLY_MESSAGE",
    # models
    "gpt_3p5_turbo",
    "gpt_3p5_turbo_16k",
    "gpt_3p5_turbo_0613",
    "gpt_3p5_turbo_16k_0613",
    "gpt_4_0314",
    "gpt_4_0613",
    "gpt_4_32k_0314",
    "gpt_4_32k_0613",
    # prompts
    "expand_prompt",
    "genius_prompt",
    "rewrite_prompt",
    "translator_prompt",
    "etymologists_prompt",
    "cyber_secrity_prompt",
    "linux_terminal_prompt",
)

from .commands import (
    cyber_secrity_command,
    etymologists_command,
    genius_command,
    linux_terminal_command,
    model_switch_command,
    reset_command,
    rewrite_command,
    translator_command,
)

from .messages import (
    NOT_PERMITED,
    NOT_ALLOWD,
    YES_OR_NO_KEYBOARD,
    TARGET_LANGUAGE_KEYBOARD,
    ASK_FOR_PERMITED,
    PROCESS_TIMEOUT,
    APPROVED_MESSAGE,
    DECLINE_MESSAGE,
    WELCOME_MESSAGE,
    NEW_CONVERSATION_MESSAGE,
    INIT_REPLY_MESSAGE,
  )

from .models import (
    gpt_3p5_turbo,
    gpt_3p5_turbo_16k,
    gpt_3p5_turbo_0613,
    gpt_3p5_turbo_16k_0613,
    gpt_4_0314,
    gpt_4_0613,
    gpt_4_32k_0314,
    gpt_4_32k_0613,
  )

from .prompts import (
    expand_prompt,
    genius_prompt,
    rewrite_prompt,
    translator_prompt,
    etymologists_prompt,
    cyber_secrity_prompt,
    linux_terminal_prompt,
  )
