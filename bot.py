import os
import telebot
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Ex: https://meu-bot-telegram.onrender.com

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    print("ERRO: TELEGRAM_BOT_TOKEN ou GEMINI_API_KEY não encontrados.")
    exit(1)

# Inicializa o bot e o Flask
app = Flask(__name__)
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

# Rota do webhook para receber updates do Telegram
@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return 'OK', 200

# Rota de health check para o Render manter o serviço ativo
@app.route('/', methods=['GET'])
def health_check():
    return 'Bot está rodando!', 200

# Configura o webhook e inicia o servidor
if __name__ == '__main__':
    if WEBHOOK_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
        print(f"Webhook configurado: {WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    else:
        print("AVISO: WEBHOOK_URL não definida. Usando polling para desenvolvimento local.")
        bot.infinity_polling()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
