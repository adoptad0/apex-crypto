import os
import sqlite3
import telebot
from flask import Flask
from threading import Thread

# Servidor web básico para mantener activo el bot en Render
app = Flask('')

@app.route('/')
def home():
    return "Apex Crypto Bot is online! 🚀"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = '8976336886:AAG_76KLFWW9HGv9GIquqqiiGWDcDuOQw4A'
bot = telebot.TeleBot(TOKEN)
DB_NAME = 'simulator.db'

# Inicia la base de datos de usuarios si no existe
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 100.0,
            invested REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

# Obtiene los datos del usuario o lo registra con $100 gratis de prueba
def get_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT balance, invested FROM users WHERE telegram_id = ?', (telegram_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute('INSERT INTO users (telegram_id, balance, invested) VALUES (?, 100.0, 0.0)', (telegram_id,))
        conn.commit()
        balance, invested = 100.0, 0.0
    else:
        balance, invested = row
    conn.close()
    return balance, invested

# Actualiza los saldos del usuario en la base de datos
def update_user(telegram_id, balance, invested):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = ?, invested = ? WHERE telegram_id = ?', (balance, invested, telegram_id))
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    telegram_id = message.from_user.id
    get_user(telegram_id)  # Registra al usuario si es nuevo
    welcome_text = (
        "Welcome to **Apex Crypto**! 🚀\n\n"
        "Here is your virtual investment simulator. We started you with **$100.00 USD** in demo money!\n\n"
        "Commands:\n"
        "• /balance - Check your wallet\n"
        "• /invest <amount> - Invest money to earn 5% daily\n"
        "• /claim - Claim your 5% daily profit\n"
        "• /withdraw <amount> - Withdraw demo money (Min. $50)"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['balance'])
def check_balance(message):
    telegram_id = message.from_user.id
    balance, invested = get_user(telegram_id)
    balance_text = (
        "💳 **Your Apex Wallet**:\n\n"
        f"• Available Balance: ${balance:.2f} USD\n"
        f"• Invested Funds: ${invested:.2f} USD"
    )
    bot.reply_to(message, balance_text, parse_mode='Markdown')

@bot.message_handler(commands=['invest'])
def invest_money(message):
    telegram_id = message.from_user.id
    balance, invested = get_user(telegram_id)
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Usage: /invest <amount>\nExample: `/invest 50`", parse_mode='Markdown')
            return
        
        amount = float(args[1])
        if amount <= 0:
            bot.reply_to(message, "Please enter an amount greater than 0.")
            return
            
        if amount > balance:
            bot.reply_to(message, f"You don't have enough balance. Your balance is ${balance:.2f} USD.")
            return
            
        new_balance = balance - amount
        new_invested = invested + amount
        update_user(telegram_id, new_balance, new_invested)
        
        bot.reply_to(message, f"Successfully invested **${amount:.2f} USD**! 📈\nYour daily profit will accumulate based on this.", parse_mode='Markdown')
        
    except ValueError:
        bot.reply_to(message, "Please enter a valid number.")

@bot.message_handler(commands=['claim'])
def claim_profit(message):
    telegram_id = message.from_user.id
    balance, invested = get_user(telegram_id)
    
    if invested <= 0:
        bot.reply_to(message, "You don't have any active investments. Use /invest to start earning.")
        return
        
    profit = invested * 0.05
    new_balance = balance + profit
    update_user(telegram_id, new_balance, invested)
    
    bot.reply_to(message, f"Claimed **${profit:.2f} USD** in profit! 💰\nAdded to your available balance.", parse_mode='Markdown')

@bot.message_handler(commands=['withdraw'])
def withdraw_money(message):
    telegram_id = message.from_user.id
    balance, invested = get_user(telegram_id)
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Usage: /withdraw <amount>\nExample: `/withdraw 50`", parse_mode='Markdown')
            return
            
        amount = float(args[1])
        if amount < 50:
            bot.reply_to(message, "The minimum withdrawal amount is **$50.00 USD**.", parse_mode='Markdown')
            return
            
        if amount > balance:
            bot.reply_to(message, f"Insufficient funds. Your available balance is ${balance:.2f} USD.")
            return
            
        new_balance = balance - amount
        update_user(telegram_id, new_balance, invested)
        
        bot.reply_to(message, f"Withdrawal of **${amount:.2f} USD** has been requested successfully! 💸\n(This is a simulation, no real money was sent).", parse_mode='Markdown')
        
    except ValueError:
        bot.reply_to(message, "Please enter a valid number.")

if __name__ == '__main__':
    init_db()
    keep_alive()
    print("Apex Crypto Bot is starting...")
    bot.infinity_polling()
