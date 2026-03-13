import os
import telebot
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request
import logging

# Configura o logging para ver detalhes no Render
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    logger.error("ERRO: TELEGRAM_BOT_TOKEN ou GEMINI_API_KEY não encontrados.")
    exit(1)

# Inicializa o bot e o Flask
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, threaded=False) # threaded=False para evitar problemas com Gunicorn

# Inicializa o Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini API configurado com sucesso.")
except Exception as e:
    logger.error(f"Erro ao configurar Gemini AI: {str(e)}")

# Armazena histórico de conversas
chat_histories = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    logger.info(f"Recebido comando {message.text} de {message.chat.id}")
    try:
        bot.reply_to(message, "Olá! Eu sou a sua IA pessoal conectada ao Gemini. Como posso ajudar você hoje?")
        chat_histories[message.chat.id] = model.start_chat(history=[])
        logger.info("Boas-vindas enviada e chat iniciado.")
    except Exception as e:
        logger.error(f"Erro no handler de welcome: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id
    user_text = message.text
    logger.info(f"Recebida mensagem: '{user_text}' do chat: {chat_id}")

    if chat_id not in chat_histories:
        chat_histories[chat_id] = model.start_chat(history=[])

    chat = chat_histories[chat_id]

    try:
        bot.send_chat_action(chat_id, 'typing')
        logger.debug("Enviando solicitação ao Gemini...")
        response = chat.send_message(user_text)
        logger.debug(f"Resposta do Gemini recebida: {response.text[:50]}...")
        bot.reply_to(message, response.text)
    except Exception as e:
        logger.error(f"Erro ao processar mensagem Gemini: {str(e)}")
        try:
            bot.reply_to(message, f"Desculpe, ocorreu um erro: {str(e)}")
        except:
            logger.error("Falha ao enviar mensagem de erro de volta ao usuário.")

# Rota do webhook para receber updates do Telegram
@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    logger.debug("Requisição recebida no Webhook")
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        logger.debug("Update processado com sucesso pelo bot")
        return 'OK', 200
    except Exception as e:
        logger.error(f"Erro ao processar requisição POST no webhook: {str(e)}")
        return 'Error', 500

# Rota de health check
@app.route('/', methods=['GET'])
def health_check():
    return 'Bot está rodando com logs detalhados!', 200

# Configura o webhook na inicialização do módulo
if WEBHOOK_URL:
    try:
        bot.remove_webhook()
        base_url = WEBHOOK_URL.rstrip('/')
        full_webhook_url = f"{base_url}/{TELEGRAM_BOT_TOKEN}"
        bot.set_webhook(url=full_webhook_url)
        logger.info(f"Webhook configurado: {full_webhook_url}")
    except Exception as e:
        logger.error(f"Erro crítico ao configurar Webhook: {str(e)}")

if __name__ == '__main__':
    if not WEBHOOK_URL:
        bot.infinity_polling()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
