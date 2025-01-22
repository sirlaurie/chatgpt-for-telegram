from openai import AsyncOpenAI
import google.generativeai as genai
# from groq import AsyncGroq

from ..constants.models import (
    gpt_3p5_turbo,
    gpt_3p5_turbo_1106,
    gpt_4o,
    gpt_4_turbo,
    gemini_2_flash,
    gemini_experimental,
    gemini_2_flash_thinking,
)

openai_client = AsyncOpenAI()
# groq_client = AsyncGroq()
genai.configure()


llm_services = {
    gpt_4o: openai_client,
    gpt_4_turbo: openai_client,
    gpt_3p5_turbo: openai_client,
    gpt_3p5_turbo_1106: openai_client,
    gemini_2_flash: genai,
    gemini_experimental: genai,
    gemini_2_flash_thinking: genai,
}
