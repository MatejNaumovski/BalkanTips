import telebot
import requests
import os
import threading
from flask import Flask

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
COMMUNITY_ID = -100xxxxxxxxxx # Put your Group ID here
MY_TON_WALLET = "YOUR_WALLET_ADDRESS" 

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Dictionary for language content
LANGS = {
    "en": {"btn": "English 🇬🇧", "msg": "Send payment to this wallet using TON only: "},
    "sr": {"btn": "Srpski 🇷🇸", "msg": "Pošaljite uplatu na ovaj novčanik koristeći samo TON: "},
    "mk": {"btn": "Македонски 🇲🇰", "msg": "Испратете уплата на овој паричник користејќи исклучиво TON: "},
    "sq": {"btn": "Shqip 🇦🇱", "msg": "Dërgoni pagesën në këtë portofol duke përdorur vetëm TON: "}
}

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    for code, data in LANGS.items():
        markup.add(telebot.types.InlineKeyboardButton(text=data["btn"], callback_data=f"lang_{code}"))
    bot.send_message(message.chat.id, "Please select your language / Ве молиме изберете јазик:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.startswith("lang_"):
        lang = call.data.split("_")[1]
        user_id = call.from_user.id
        unique_comment = f"JOIN-{user_id}"
        
        text = (f"{LANGS[lang]['msg']}\n\n`{MY_TON_WALLET}`\n\n"
                f"Memo/Comment: `{unique_comment}`\n\n"
                "⚠️ Only TON is accepted. Payments in other currencies will be lost.")
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="Verify Payment", callback_data=f"verify_{user_id}"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text=text, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("verify_"):
        # Keep your existing verification logic here (the check_blockchain_for_memo function)
        pass 

# Keep the rest of your logic (check_blockchain_for_memo, run_bot, flask)
