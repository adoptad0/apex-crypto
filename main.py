import os
import sqlite3
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import datetime

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
DB_NAME = 'simulator_v2.db'  # Cambiado para evitar conflictos de base de datos

# Inicia la base de datos de usuarios si no existe
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 100.0,
            invested REAL DEFAULT 0.0,
            last_invest_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Obtiene los datos del usuario o lo registra
def get_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT balance, invested, last_invest_time FROM users WHERE telegram_id = ?', (telegram_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute('INSERT INTO users (telegram_id, balance, invested, last_invest_time) VALUES (?, 100.0, 0.0, NULL)', (telegram_id,))
        conn.commit()
        balance, invested, last_invest_time = 100.0, 0.0, None
    else:
        balance, invested, last_invest_time = row
    conn.close()
    return balance, invested, last_invest_time

# Actualiza los saldos del usuario en la base de datos
def update_user(telegram_id, balance, invested, last_invest_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = ?, invested = ?, last_invest_time = ? WHERE telegram_id = ?', (balance, invested, last_invest_time, telegram_id))
    conn.commit()
    conn.close()

# Menú principal con botones
def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_balance = types.KeyboardButton("💳 Balance")
    btn_invest = types.KeyboardButton("📈 Invest")
    btn_deposit = types.KeyboardButton("📥 Deposit")
    btn_claim = types.KeyboardButton("💰 Claim Profit")
    btn_withdraw = types.KeyboardButton("💸 Withdraw")
    markup.add(btn_balance, btn_invest, btn_deposit, btn_claim, btn_withdraw)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    telegram_id = message.from_user.id
    get_user(telegram_id)  # Registra al usuario si es nuevo
    welcome_text = (
        "Welcome to **Apex Crypto**! 🚀\n\n"
        "Here is your investment dashboard. We started you with **$100.00 USD** in demo money!\n\n"
        "Use the buttons below to navigate your account:"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == "💳 Balance")
def check_balance(message):
    telegram_id = message.from_user.id
    balance, invested, last_invest_time = get_user(telegram_id)
    
    profit_percentage = 0.0
    pending_profit = 0.0
    
    if invested > 0 and last_invest_time:
        try:
            start_time = datetime.datetime.fromisoformat(last_invest_time)
            now = datetime.datetime.now()
            diff_minutes = (now - start_time).total_seconds() / 60.0
            # Para simulación rápida, cada minuto da un 0.1% de ganancia
            profit_percentage = diff_minutes * 0.1
            pending_profit = invested * (profit_percentage / 100.0)
        except Exception:
            pass

    balance_text = (
        "💳 **Your Apex Wallet**:\n\n"
        f"• Available Balance: ${balance:.2f} USD\n"
        f"• Invested Funds: ${invested:.2f} USD\n\n"
        f"📊 **Investment Growth**:\n"
        f"• Profit Rate: **5.00% Daily**\n"
        f"• Current Growth: **+{profit_percentage:.3f}%**\n"
        f"• Unclaimed Profit: **${pending_profit:.4f} USD**"
    )
    bot.reply_to(message, balance_text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == "📥 Deposit")
def show_deposit_addresses(message):
    deposit_text = (
        "📥 **Deposit Funds to Your Account**:\n\n"
        "Please send your deposit to one of the addresses below. "
        "Once confirmed, your balance will be credited:\n\n"
        "• **BTC**:\n`bc1q46f64ny6k85954ndlzvh32kuc40mqdhxw7fxls`\n\n"
        "• **ETH / ERC-20** (ETH, USDT, USDC):\n`0xfC1dF2CBD973D1234d2108996Cc8694d7489dDdB`\n\n"
        "• **Polygon** (MATIC, USDT, USDC):\n`0xfC1dF2CBD973D1234d2108996Cc8694d7489dDdB`\n\n"
        "• **BNB Chain** (BNB, USDT, USDC):\n`0xfC1dF2CBD973D1234d2108996Cc8694d7489dDdB`\n\n"
        "• **BASE** (ETH, USDT, USDC):\n`0xfC1dF2CBD973D1234d2108996Cc8694d7489dDdB`\n\n"
        "• **TRON** (TRX, USDT):\n`TWgDYwExwx7G3Cr2kY6xj18tdfd6KM2fLU`\n\n"
        "• **XRP**:\n`rh6GEmHCXDUUJsCrnr3HusmUXkWNGjFyhN`\n\n"
        "• **Solana** (SOL, USDT, USDC):\n`DM3ER7SdSAH6GZwisRVXFashLnPXpeaFKmrKEjDrpTPK`"
    )
    bot.reply_to(message, deposit_text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == "📈 Invest")
def invest_prompt(message):
    msg = bot.reply_to(message, "Please type the amount you want to invest (Example: 50):", reply_markup=types.ForceReply(selective=True))
    bot.register_next_step_handler(msg, process_invest)

def process_invest(message):
    telegram_id = message.from_user.id
    balance, invested, last_invest_time = get_user(telegram_id)
    
    try:
        amount = float(message.text)
        if amount <= 0:
            bot.reply_to(message, "Please enter an amount greater than 0.")
            return
            
        if amount > balance:
            bot.reply_to(message, f"You don't have enough balance. Your balance is ${balance:.2f} USD.")
            return
            
        new_balance = balance - amount
        new_invested = invested + amount
        now_str = datetime.datetime.now().isoformat()
        update_user(telegram_id, new_balance, new_invested, now_str)
        
        bot.reply_to(message, f"Successfully invested **${amount:.2f} USD**! 📈\nYour daily profit will now start accumulating.", parse_mode='Markdown', reply_markup=main_menu_keyboard())
        
    except ValueError:
        bot.reply_to(message, "Please enter a valid number.")

@bot.message_handler(func=lambda message: message.text == "💰 Claim Profit")
def claim_profit(message):
    telegram_id = message.from_user.id
    balance, invested, last_invest_time = get_user(telegram_id)
    
    if invested <= 0 or not last_invest_time:
        bot.reply_to(message, "You don't have any active investments. Use 'Invest' to start earning.")
        return
        
    try:
        start_time = datetime.datetime.fromisoformat(last_invest_time)
        now = datetime.datetime.now()
        diff_minutes = (now - start_time).total_seconds() / 60.0
        profit_percentage = diff_minutes * 0.1
        profit = invested * (profit_percentage / 100.0)
    except Exception:
        profit = 0.0
    
    if profit <= 0:
        bot.reply_to(message, "No new profits to claim yet. Please wait a little longer!")
        return
        
    new_balance = balance + profit
    now_str = datetime.datetime.now().isoformat()
    update_user(telegram_id, new_balance, invested, now_str) # Reinicia el tiempo al reclamar
    
    bot.reply_to(message, f"Claimed **${profit:.4f} USD** in profit! 💰\nAdded to your available balance.", parse_mode='Markdown', reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == "💸 Withdraw")
def withdraw_prompt(message):
    msg = bot.reply_to(message, "Please type the amount you want to withdraw (Min. $50):", reply_markup=types.ForceReply(selective=True))
    bot.register_next_step_handler(msg, process_withdraw)

def process_withdraw(message):
    telegram_id = message.from_user.id
    balance, invested, last_invest_time = get_user(telegram_id)
    
    try:
        amount = float(message.text)
        if amount < 50:
            bot.reply_to(message, "The minimum withdrawal amount is **$50.00 USD**.", parse_mode='Markdown')
            return
            
        if amount > balance:
            bot.reply_to(message, f"Insufficient funds. Your available balance is ${balance:.2f} USD.")
            return
            
        new_balance = balance - amount
        update_user(telegram_id, new_balance, invested, last_invest_time)
        
        bot.reply_to(message, f"Withdrawal of **${amount:.2f} USD** has been requested successfully! 💸\n(This is a simulation, no real money was sent).", parse_mode='Markdown', reply_markup=main_menu_keyboard())
        
    except ValueError:
        bot.reply_to(message, "Please enter a valid number.")

if __name__ == '__main__':
    init_db()
    keep_alive()
    print("Apex Crypto Bot is starting...")
    bot.infinity_polling()
