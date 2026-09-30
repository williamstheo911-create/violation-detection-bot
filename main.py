import os
import telebot
from google import genai
from google.genai import types

# 1. Загрузка переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("Telegram_Token")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Missing Telegram_Token or GEMINI_API_KEY in environment variables.")

# 2. Инициализация бота и клиента Gemini
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# Промпт для поиска нарушений
VIOLATION_PROMPT = """
You are an expert compliance and document auditor. Analyze the provided image, document, or text 
for any compliance violations, discrepancies, policy breaches, or anomalies. 
Provide a clear, concise report:
1. **Status:** (Compliant / Violation Found / Needs Review)
2. **Details:** Explain what was found.
3. **Recommendation:** What action should be taken.
"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Привет! Отправьте мне фото отчета или документ, и я проверю его на наличие нарушений."
    )

# Обработка фотографий
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Используем актуальную модель gemini-3.8-flash
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[
                types.Part.from_bytes(
                    data=downloaded_file,
                    mime_type='image/jpeg',
                ),
                VIOLATION_PROMPT
            ]
        )
        
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка обработки изображения: {str(e)}")

# Обработка документов
@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = message.document.file_name or ""
        mime_type = 'application/pdf' if file_name.lower().endswith('.pdf') else 'image/jpeg'
        
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[
                types.Part.from_bytes(
                    data=downloaded_file,
                    mime_type=mime_type,
                ),
                VIOLATION_PROMPT
            ]
        )
        
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка обработки документа: {str(e)}")

if __name__ == "__main__":
    print("Бот запущен и ожидает сообщения...")
    bot.infinity_polling()
