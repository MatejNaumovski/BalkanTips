import telebot
import requests
import os
import threading
from flask import Flask

# --- ⚠️ CONFIGURATION ⚠️ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
COMMUNITY_ID = -100xxxxxxxxxx  # Replace with your real negative group ID number
MY_TON_WALLET = "UQA3n4Lgs0gJRinUW-CFbwOpILhmkUvVT-dsoXKjgMhJiGR-" # Your wallet from the image

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- COMPLETE TRANSLATION DICTIONARY ---
LANG_DATA = {
    "en": {
        "name": "English 🇬🇧",
        "text": "💰 *TON Wallet Address:*\n`{wallet}`\n\n⚠️ *IMPORTANT:* You must copy and paste the code below into the **Comment / Memo** field of your transaction, or the bot cannot track your payment:\n`{comment}`\n\n❌ *WE ONLY ACCEPT TON CRYPTOCURRENCY!* Payments in any other coin will be completely lost.\n\nTap the verification button below as soon as your wallet says sent!",
        "verify_btn": "🔄 Verify My Payment",
        "success": "✅ Payment Confirmed! Tap this link to join the premium community: {link}",
        "fail": "❌ Payment not detected yet. Make sure you included the exact comment code and wait 1 minute for the blockchain."
    },
    "sr": {
        "name": "Srpski 🇷🇸",
        "text": "💰 *Adresa TON novčanika:*\n`{wallet}`\n\n⚠️ *VAŽNO:* Morate kopirati i nalepiti kod ispod u polje **Komentar / Memo** prilikom slanja transakcije, u suprotnom bot neće moći da potvrdi uplatu:\n`{comment}`\n\n❌ *PRIHVATAMO SAMO TON KRIPTOVALUTU!* Uplate u drugim valutama će бити trajno izgubljene.\n\nKliknite na dugme ispod čim vaš novčanik prikaže da je poslato!",
        "verify_btn": "🔄 Potvrdi moju uplatu",
        "success": "✅ Uplata je potvrđena! Kliknite na ovaj link da se pridružite zajednici: {link}",
        "fail": "❌ Transakcija još uvek nije pronađena. Proverite da li je komentar tačan i sačekajte 1 minut."
    },
    "mk": {
        "name": "Македонски 🇲🇰",
        "text": "💰 *Адреса на TON паричник:*\n`{wallet}`\n\n⚠️ *ВАЖНО:* Мора да го копирате и залепите кодот подолу во полето **Коментар / Memo** при плаќањето, во спротивно ботот нема да ја препознае уплатата:\n`{comment}`\n\n❌ *ПРИФАЌАМЕ ИСКЛУЧИВО TON КРИПТОВАЛУТА!* Уплатите во други валути ќе бидат трајно изгубени.\n\nПритиснете го копчето подолу штом вашиот паричник покаже дека е испратено!",
        "verify_btn": "🔄 Потврди ја мојата уплата",
        "success": "✅ Уплатата е потврдена! Кликнете на овој линк за да се приклучите: {link}",
        "fail": "❌ Трансакцијата сè уште не е пронајдена. Проверете го коментарот и почекајте 1 минута."
    },
    "sq": {
        "name": "Shqip 🇦🇱",
        "text": "💰 *Adresa e Portofolit TON:*\n`{wallet}`\n\n⚠️ *E RËNDËSISHME:* Duhet të kopjoni dhe ngjitni kodin e mëposhtëm në fushën **Comment / Memo** të transaksionit tuaj, përndryshe boti nuk mund ta gjurmojë pagesën:\n`{comment}`\n\n❌ *PRANOJMË VETËM KRIPTOVALUTË TON!* Pagesat në monedha të tjera do të humbasin plotësisht.\n\nShtypni butonin e mëposhtëm sapo portofoli juaj të thotë u dërgua!",
        "verify_btn": "🔄 Verifiko Pagesën Time",
        "success": "✅ Pagesa u konfirmua! Klikoni këtë link për t'u bashkuar: {link}",
        "fail": "❌ Transaksioni nuk u gjet ende. Sigurohuni që komenti është i saktë dhe prisni 1 minutë."
    }
}

@app.route('/')
def home():
    return "Bot is active!", 200

# 1. When user presses /start, present clean language buttons
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for code, data in LANG_DATA.items():
        markup.add(telebot.types.InlineKeyboardButton(data["name"], callback_data=f"lang_{code}"))
    
    bot.send_message(message.chat.id, "Please select your language / Изберете јазик:", reply_markup=markup)

# 2. When user clicks a language, swap text and make the button match that language
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_language_selection(call):
    lang_code = call.data.split("_")[1]
    user_id = call.from_user.id
    unique_comment = f"JOIN-{user_id}"
    
    # Fill variables into the specific language template
    formatted_text = LANG_DATA[lang_code]["text"].format(
        wallet=MY_TON_WALLET,
        comment=unique_comment
    )
    
    # Create the verification button in the correct language
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        text=LANG_DATA[lang_code]["verify_btn"], 
        callback_data=f"verify_{user_id}_{lang_code}"
    ))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        text=formatted_text, 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# 3. Handle checking the blockchain when they click verify
@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def handle_verification(call):
    _, user_id, lang_code = call.data.split("_")
    bot.answer_callback_query(call.id)
    
    expected_memo = f"JOIN-{user_id}"
    
    if check_blockchain_for_memo(expected_memo):
        try:
            invite = bot.create_chat_invite_link(chat_id=COMMUNITY_ID, member_limit=1)
            success_msg = LANG_DATA[lang_code]["success"].format(link=invite.invite_link)
            bot.send_message(call.message.chat.id, success_msg)
        except Exception:
            bot.send_message(call.message.chat.id, "Error creating invite link. Please contact admin.")
    else:
        bot.send_message(call.message.chat.id, LANG_DATA[lang_code]["fail"])

def check_blockchain_for_memo(target_comment):
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_TON_WALLET}&limit=20"
    try:
        response = requests.get(url).json()
        if response.get("ok"):
            for tx in response["result"]:
                in_msg = tx.get("in_msg", {})
                if in_msg.get("message") == target_comment:
                    return True
    except Exception:
        pass
    return False

def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
