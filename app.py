import telebot
import requests
import threading
import os
from flask import Flask

# --- ⚠️ CONFIGURATION ⚠️ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
COMMUNITY_ID = -100203997550617
MY_TON_WALLET = "UQA3n4Lgs0gJRinUW-CFbwOpILhmkUvVT-dsoXKjgMhJiGR-"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 🌐 This dummy webpage tricks Render into keeping your app active
@app.route('/')
def home():
    return "Bot status: Running smoothly!", 200

@bot.message_handler(commands=['start'])
def welcome_user(message):
    user_id = message.from_user.id
    unique_comment = f"JOIN-{user_id}"
    
    payment_instructions = (
        f"👋 *Welcome!*\n\n"
        f"To join the private community, send your payment directly to my wallet:\n\n"
        f"💰 *Wallet Address:* \n`{MY_TON_WALLET}`\n\n"
        f"⚠️ *IMPORTANT:* You must copy and paste the code below into the **Comment / Memo** field of your transaction, otherwise the bot cannot track your payment:\n"
        f"`{unique_comment}`\n\n"
        f"Tap the verification button below as soon as your wallet says sent!"
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text="🔄 Verify My Payment", callback_data=f"verify_{user_id}"))
    bot.send_message(message.chat.id, payment_instructions, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def process_verification(call):
    user_id = call.data.split("_")[1]
    bot.answer_callback_query(call.id, "Scanning blockchain ledger...")
    
    expected_memo = f"JOIN-{user_id}"
    
    if check_blockchain_for_memo(expected_memo):
        try:
            invite = bot.create_chat_invite_link(chat_id=COMMUNITY_ID, member_limit=1)
            bot.send_message(call.message.chat.id, f"✅ Payout Confirmed! Tap this link to join: {invite.invite_link}")
        except Exception as e:
            bot.send_message(call.message.chat.id, "❌ Paid, but link generation failed. Message the owner.")
    else:
        bot.send_message(call.message.chat.id, "❌ Payout not detected yet. Make sure you included the exact text comment and wait 1 minute for the network to process.")

def check_blockchain_for_memo(target_comment):
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_TON_WALLET}&limit=20"
    try:
        response = requests.get(url).json()
        if response.get("ok"):
            for tx in response["result"]:
                in_msg = tx.get("in_msg", {})
                message_text = in_msg.get("message", "")
                if message_text == target_comment:
                    return True
    except Exception as e:
        pass
    return False

# Runs the Telegram listener in a background thread
def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot, daemon=True).start()

# Flask requires an entry point for production servers on Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
