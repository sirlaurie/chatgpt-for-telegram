from openai import AsyncOpenAI
import google.generativeai as genai
from groq import AsyncGroq

from ..constants.models import (
    gpt_3p5_turbo,
    gpt_3p5_turbo_1106,
    gpt_4,
    gpt_4_turbo,
    gemini_pro,
    gemini_1p5_pro,
    llama3,
    mixtral_8x7b,
)

openai_client = AsyncOpenAI()
groq_client = AsyncGroq()
genai.configure()


llm_services = {
    gpt_4: openai_client,
    gpt_4_turbo: openai_client,
    gpt_3p5_turbo: openai_client,
    gpt_3p5_turbo_1106: openai_client,
    gemini_pro: genai,
    gemini_1p5_pro: genai,
    llama3: groq_client,
    mixtral_8x7b: groq_client,
}
