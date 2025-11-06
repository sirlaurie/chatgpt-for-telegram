from openai import AsyncOpenAI
import google.generativeai as genai

from ..constants.models import (
    # OpenAI models
    gpt_4o,
    gpt_4o_mini,
    gpt_4_turbo,
    # Gemini models
    gemini_2p5_flash,
    gemini_2p5_flash_thinking,
    gemini_exp_1206,
)

openai_client = AsyncOpenAI()
genai.configure()


llm_services = {
    # OpenAI models
    gpt_4o: openai_client,
    gpt_4o_mini: openai_client,
    gpt_4_turbo: openai_client,
    # Gemini models
    gemini_2p5_flash: genai,
    gemini_2p5_flash_thinking: genai,
    gemini_exp_1206: genai,
}
