from openai import AsyncOpenAI
import google.generativeai as genai

from ..constants.models import (
    # OpenAI models
    gpt_4o,
    gpt_4o_mini,
    gpt_4p1,
    # Gemini models
    gemini_2p5_flash,
    gemini_2p5_pro,
    gemini_flash_latest,
)

openai_client = AsyncOpenAI()
genai.configure()


llm_services = {
    # OpenAI models
    gpt_4o: openai_client,
    gpt_4o_mini: openai_client,
    gpt_4p1: openai_client,
    # Gemini models
    gemini_2p5_flash: genai,
    gemini_2p5_pro: genai,
    gemini_flash_latest: genai,
}
