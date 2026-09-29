import os
import telebot
from google import genai
from google.genai import types
import io
import pypdf

# Get credentials from Railway environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    print("Error: Missing TELEGRAM_BOT_TOKEN or GEMINI_API_KEY in environment variables.")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# Default violation rulebook
DEFAULT_RULES = (
    "1. Check for missing mandatory legal clauses, weights, or liability limits.\n"
    "2. Detect safety gear violations (e.g., missing hardhats, vests) in pictures.\n"
    "3. Look for expired dates, incorrect formatting, or unauthorized terms."
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hello! Send me any picture (like an inspection report or safety photo) or a PDF document, and I will check it for violations instantly!")

@bot.message_handler(content_types=['photo', 'document'])
def handle_incoming_file(message):
    try:
        bot.reply_to(message, "🔍 Analyzing file for violations, please wait...")
        
        file_info = None
        file_extension = ""
        
        # Handle photos sent directly to the chat
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            file_extension = "jpg"
            
        # Handle documents/PDFs sent as files
        elif message.content_type == 'document':
            file_info = bot.get_file(message.document.file_id)
            file_extension = message.document.file_name.split('.')[-1].lower()

        downloaded_file = bot.download_file(file_info.file_path)
        
        contents = []
        prompt = (
            f"You are an expert compliance auditor. Analyze the attached file strictly against these rules:\n"
            f"{DEFAULT_RULES}\n\n"
            f"Provide a clear, structured report listing:\n"
            f"1. Overall Status (PASS / FAIL)\n"
            f"2. Detected Violations (with severity and descriptions)\n"
            f"3. Recommendations for Correction"
        )
        contents.append(prompt)

        # Attach image to Gemini
        if file_extension in ["png", "jpg", "jpeg"]:
            contents.append(types.Part.from_bytes(data=downloaded_file, mime_type=f"image/{file_extension}"))
            
        # Attach PDF text to Gemini
        elif file_extension == "pdf":
            reader = pypdf.PdfReader(io.BytesIO(downloaded_file))
            pdf_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"
            contents.append(f"Document Text Content:\n{pdf_text}")
        else:
            bot.reply_to(message, "⚠️ Unsupported file format. Please send an image (JPG/PNG) or a PDF.")
            return

        # Call Gemini 1.5 Flash model
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=contents
        )

        report = f"🚨 *Violation & Compliance Report*\n\n{response.text}"
        
        # Truncate if message is too long for Telegram
        if len(report) > 4000:
            report = report[:4000] + "\n\n[Report truncated due to length]"

        bot.reply_to(message, report, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred during analysis: {e}")

if __name__ == '__main__':
    print("Bot is polling for messages...")
    bot.infinity_polling()
