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

# --- LANGUAGE DATA ---
# Simple dictionary for your translations
LANG_DATA = {
    "en": {"name": "English 🇬🇧", "text": "Send payment to this wallet using TON only: "},
    "sr": {"name": "Srpski 🇷🇸", "text": "Pošaljite uplatu na ovaj novčanik koristeći samo TON: "},
    "mk": {"name": "Македонски 🇲🇰", "text": "Испратете уплата на овој паричник користејќи исклучиво TON: "},
    "sq": {"name": "Shqip 🇦🇱", "text": "Dërgoni pagesën në këtë portofol duke përdorur vetëm TON: "}
}

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    # Create buttons for each language
    for code, data in LANG_DATA.items():
        button = telebot.types.InlineKeyboardButton(data["name"], callback_data=f"lang_{code}")
        markup.add(button)
    
    bot.send_message(message.chat.id, "Select your language / Изберете јазик:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_lang(call):
    lang_code = call.data.split("_")[1]
    user_id = call.from_user.id
    unique_comment = f"JOIN-{user_id}"
    
    # The message the user gets after picking a language
    reply_text = (f"{LANG_DATA[lang_code]['text']}\n\n"
                  f"Address: `{MY_TON_WALLET}`\n\n"
                  f"Comment: `{unique_comment}`\n\n"
                  "⚠️ ONLY TON IS ACCEPTED.")
    
    # Send the final payment instructions
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text=reply_text, parse_mode="Markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
