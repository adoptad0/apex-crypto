import telebot

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
    print("Apex Crypto Bot is starting...")
    bot.infinity_polling()
