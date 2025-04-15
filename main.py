import os
import logging
import datetime
import tempfile
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from openai import OpenAI

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

client = OpenAI(api_key=OPENAI_API_KEY)

PROMPT_FILE = "prompt.md"
with open(PROMPT_FILE, encoding="utf-8") as f:
    BASE_PROMPT = f.read()

async def transcribe_voice(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    return transcript

async def ask_gpt(user_input):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": BASE_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0.5
    )
    return response.choices[0].message.content

@dp.message_handler(content_types=types.ContentType.VOICE)
async def handle_voice(message: types.Message):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
        file_path = tmp.name
    file = await bot.get_file(message.voice.file_id)
    await bot.download_file(file.file_path, file_path)
    text = await transcribe_voice(file_path)
    await handle_text_input(message, text)

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    await handle_text_input(message, message.text)

async def handle_text_input(message, text):
    await message.answer("🔎 Анализирую ваши мысли...")
    gpt_response = await ask_gpt(text)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    message_text = f"📅 **Дата:** {now}\n\n{gpt_response}"
    await message.answer(message_text, parse_mode="Markdown")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)