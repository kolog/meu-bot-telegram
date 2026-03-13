import os
import telebot
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    print("ERRO: TELEGRAM_BOT_TOKEN ou GEMINI_API_KEY não encontrados nas variáveis de ambiente.")
    exit(1)

# Inicializa o bot do Telegram
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Inicializa o Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Armazena histórico de conversas
chat_histories = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Olá! Eu sou a sua IA pessoal conectada ao Gemini. Como posso ajudar você hoje?")
    chat_histories[message.chat.id] = model.start_chat(history=[])

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id
    user_text = message.text
    
    if chat_id not in chat_histories:
        chat_histories[chat_id] = model.start_chat(history=[])
        
    chat = chat_histories[chat_id]
    
    try:
        bot.send_chat_action(chat_id, 'typing')
        response = chat.send_message(user_text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}")

if __name__ == '__main__':
    print("Bot iniciado e rodando!")
    bot.infinity_polling()
