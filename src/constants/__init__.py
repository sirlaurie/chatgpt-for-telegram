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
    "document_command",
    "gen_image_command",
    "admin_command",
    # constant
    "SUPPPORTED_FILE",
    "WAITING",
    "PERMITTED",
    "PREMIUM",
    "APPROVE",
    "DECLINE",
    "UPGRADE",
    "DOWNGRADE",
    "WAITING_COLUMN",
    "ALLOW_COLUMN",
    "PREMIUM_COLUMN",
    # messages
    "NOT_PERMITED",
    "NOT_ALLOWD",
    "ASK_FOR_PERMITED",
    "PROCESS_TIMEOUT",
    "APPROVED_MESSAGE",
    "DECLINE_MESSAGE",
    "UPGRADE_MESSAGE",
    "DOWNGRANDE_MESSAGE",
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
    document_command,
    gen_image_command,
    admin_command,
)

from .constant import (
    SUPPPORTED_FILE,
    WAITING,
    PERMITTED,
    PREMIUM,
    APPROVE,
    DECLINE,
    UPGRADE,
    DOWNGRADE,
    WAITING_COLUMN,
    ALLOW_COLUMN,
    PREMIUM_COLUMN,
)

from .messages import (
    NOT_PERMITED,
    NOT_ALLOWD,
    ASK_FOR_PERMITED,
    PROCESS_TIMEOUT,
    APPROVED_MESSAGE,
    DECLINE_MESSAGE,
    UPGRADE_MESSAGE,
    DOWNGRANDE_MESSAGE,
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
