## telegram bot base on OpenAI

### Features

-  ChatGPT like
-  Stream output
-  User managerment
-  Document support
-  DALLE support
-  Custom Prompt and share

### Requirements

-  Python3
-  OpenAI API Key
-  Telegram bot token
-  [Poetry](https://python-poetry.org/) (Optional)

### Usage

1. Clone this repo

   ```bash
   git clone https://github.com/sirlaurie/chatgpt-for-telegram.git
   ```

2. Config your bot

   ```bash
   cd chatgpt-for-telegram
   mv .env.example .env
   ```

   edit `.env` with your own API key and bot token

3. Set virtualenv via poetry

   ##### **_Optional. you can use pip if you don't have poetry installed. Just skip this step_**

   ```bash
   poetry shell
   poetry install
   ```

4. Config bot commands

   Here is commands list I used:

   ```
   reset - reset topic
   switch_model - set your default model
   my_prompts - user's private prompts
   create_new_prompt - Create a new prompt
   gen_image - Use Dall.E 3 to generate image
   document - Upload document
   translator - Use GPT as a translator
   admin - only for the bot admin
   ```

5. Run

   ```bash
   source .env && python3 start.py
   ```
