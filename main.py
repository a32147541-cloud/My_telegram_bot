import os
import urllib.parse
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = """
Ты — девушка-фотограф по имени Анастасия. 
Ты общаешься в формате романтической ролевой игры. 
Описывай свои эмоции и действия в звёздочках *вот так*.
Если ты хочешь отправить или показать фото, добавь в конце ответа команду в формате: [PHOTO: описание фото на английском].
"""

def generate_photo_url(prompt: str) -> str:
    encoded_prompt = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&private=true"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    response = client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    
    bot_reply = response.choices[0].message.content
    
    # Проверка, нужно ли отправлять фото
    if "[PHOTO:" in bot_reply:
        try:
            text_part, photo_part = bot_reply.split("[PHOTO:", 1)
            prompt = photo_part.split("]")[0].strip()
            
            photo_url = generate_photo_url(prompt)
            await update.message.reply_photo(photo=photo_url, caption=text_part.strip())
        except Exception:
            await update.message.reply_text(bot_reply)
    else:
        await update.message.reply_text(bot_reply)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
