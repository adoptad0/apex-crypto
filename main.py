import os
import telebot
from flask import Flask
from threading import Thread

# Creamos un mini servidor web para que Render no apague el bot
app = Flask('')

@app.route('/')
def home():
    return "Apex Crypto Bot is online! 🚀"

def run():
    # Render nos da un puerto automáticamente en las variables de entorno
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = '8976336886:AAG_76KLFWW9HGv9GIquqqiiGWDcDuOQw4A'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Welcome to **Apex Crypto**! 🚀\n\n"
        "I'm your assistant to help you learn about crypto investments.\n"
        "Try using the command /prices to see market info!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['prices'])
def send_prices(message):
    prices_text = (
        "📊 **Current Market Prices (Placeholder)**:\n\n"
        "• Bitcoin (BTC): $64,200 USD\n"
        "• Ethereum (ETH): $3,450 USD\n"
        "• Solana (SOL): $140 USD\n\n"
        "Soon you will be able to see real-time updates here!"
    )
    bot.reply_to(message, prices_text, parse_mode='Markdown')

if __name__ == '__main__':
    # Iniciamos el servidor web en segundo plano
    keep_alive()
    print("Apex Crypto Bot is starting...")
    bot.infinity_polling()
