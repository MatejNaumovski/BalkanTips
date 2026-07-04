import telebot
import requests
import os
import threading
import time
from flask import Flask

# --- ⚠️ CONFIGURATION ⚠️ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
COMMUNITY_ID = -1003997550617
MY_TON_WALLET = "UQA3n4Lgs0gJRinUW-CFbwOpILhmkUvVT-dsoXKjgMhJiGR-"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- TRANSLATION DICTIONARY (UPDATED WITH TON/GRAM) ---
LANG_DATA = {
    "en": {
        "name": "English 🇬🇧",
        "text": "💰 *Monthly Subscription Fee: 50 EUR*\n\n*Your dynamic amount to send right now:* `{ton_amount:.2f}` *Toncoin (TON) / Gram (GRAM)*\n\n*Wallet Address:*\n`{wallet}`\n\n⚠️ *IMPORTANT:* You must copy and paste the code below into the **Comment / Memo** field of your transaction, or the bot cannot track your payment:\n`{comment}`\n\n❌ *WE ONLY ACCEPT TON / GRAM* (Payments in other coins will be lost).\n\nTap the verification button below as soon as your wallet says sent!",
        "verify_btn": "🔄 Verify My Subscription",
        "success": "✅ Subscription Confirmed! Tap this link to join the premium community: {link}",
        "fail": "❌ Active payment not detected. Ensure you sent at least {ton_amount:.2f} Toncoin (TON) / Gram (GRAM) with the exact comment code and try again."
    },
    "sr": {
        "name": "Srpski 🇷🇸",
        "text": "💰 *Mesečna pretplata: 50 EUR*\n\n*Tačan iznos za slanje sada:* `{ton_amount:.2f}` *Toncoin (TON) / Gram (GRAM)*\n\n*Adresa novčanika:*\n`{wallet}`\n\n⚠️ *VAŽNO:* Morate kopirati i nalepiti kod ispod u polje **Komentar / Memo** prilikom slanja transakcije, u suprotnom bot neće moći da potvrdi uplatu:\n`{comment}`\n\n❌ *PRIHVATAMO SAMO TON / GRAM* (Uplate u drugim valutama će biti trajno izgubljene).\n\nKliknite na dugme ispod čim vaš novčanik prikaže da je poslato!",
        "verify_btn": "🔄 Potvrdi moju pretplatu",
        "success": "✅ Pretplata potvrđena! Kliknite na ovaj link da se pridružite: {link}",
        "fail": "❌ Aktivna uplata nije pronađena. Proverite da li ste poslali najmanje {ton_amount:.2f} Toncoin (TON) / Gram (GRAM) sa tačnim komentarom i pokušajte ponovo."
    },
    "mk": {
        "name": "Македонски 🇲🇰",
        "text": "💰 *Месечна претплата: 50 EUR*\n\n*Точен износ за испраќање сега:* `{ton_amount:.2f}` *Toncoin (TON) / Gram (GRAM)*\n\n*Адреса на паричник:*\n`{wallet}`\n\n⚠️ *ВАЖНО:* Мора да го копирате и залепите кодот подолу во полето **Коментар / Memo** при плаќањето, во спротивно ботот нема да ја препознае уплатата:\n`{comment}`\n\n❌ *ПРИФАЌАМЕ ИСКЛУЧИВО TON / GRAM* (Уплатите во други валути ќе бидат трајно изгубени).\n\nПритиснете го копчето подолу штом вашиот паричник покаже дека е испратено!",
        "verify_btn": "🔄 Потврди ја мојата претплата",
        "success": "✅ Претплата е потврдена! Кликнете на овој линк за да се приклучите: {link}",
        "fail": "❌ Активна уплата не е пронајдена. Проверете дали сте испратиле најмалку {ton_amount:.2f} Toncoin (TON) / Gram (GRAM) со точниот коментар и обидете се повторно."
    },
    "sq": {
        "name": "Shqip 🇦🇱",
        "text": "💰 *Abonimi Mujor: 50 EUR*\n\n*Shuma e saktë për të dërguar tani:* `{ton_amount:.2f}` *Toncoin (TON) / Gram (GRAM)*\n\n*Adresa e Portofolit:*\n`{wallet}`\n\n⚠️ *E RËNDËSISHME:* Duhet të kopjoni dhe ngjitni kodin e mëposhtëm në fushën **Comment / Memo** të transaksionit tuaj, përndryshe boti nuk mund ta gjurmojë pagesën:\n`{comment}`\n\n❌ *PRANOJMË VETËM TON / GRAM* (Pagesat në monedha të tjera do të humbasin).\n\nShtypni butonin e mëposhtëm sapo portofoli juaj të thotë u dërgua!",
        "verify_btn": "🔄 Verifiko Abonimin Tim",
        "success": "✅ Abonimi u konfirmua! Klikoni këtë link për t'u bashkuar: {link}",
        "fail": "❌ Abonimi aktiv nuk u gjet. Sigurohuni qe keni dërguar të paktën {ton_amount:.2f} Toncoin (TON) / Gram (GRAM) me kodin e saktë dhe provoni përsëri."
    }
}

def get_required_ton(eur_amount):
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=eur"
        res = requests.get(url).json()
        ton_price = res["the-open-network"]["eur"]
        return round(eur_amount / ton_price, 2)
    except Exception:
        return round(eur_amount / 1.47, 2)

@app.route('/')
def home():
    return "Active", 200

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for code, data in LANG_DATA.items():
        markup.add(telebot.types.InlineKeyboardButton(data["name"], callback_data=f"lang_{code}"))
    bot.send_message(message.chat.id, "Please select your language / Изберете јазик:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_lang(call):
    lang_code = call.data.split("_")[1]
    user_id = call.from_user.id
    unique_comment = f"JOIN-{user_id}"
    
    ton_displayed = get_required_ton(50.0)
    
    formatted_text = LANG_DATA[lang_code]["text"].format(
        ton_amount=ton_displayed,
        wallet=MY_TON_WALLET,
        comment=unique_comment
    )
    
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def handle_verification(call):
    _, user_id, lang_code = call.data.split("_")
    bot.answer_callback_query(call.id)
    expected_memo = f"JOIN-{user_id}"
    
    ton_displayed = get_required_ton(50.0)
    ton_minimum_allowed = get_required_ton(45.0)
    
    if check_blockchain_subscription(expected_memo, ton_minimum_allowed):
        try:
            invite = bot.create_chat_invite_link(chat_id=COMMUNITY_ID, member_limit=1)
            bot.send_message(call.message.chat.id, LANG_DATA[lang_code]["success"].format(link=invite.invite_link))
        except Exception:
            bot.send_message(call.message.chat.id, "Error: Make sure the bot is an Admin in the group!")
    else:
        bot.send_message(call.message.chat.id, LANG_DATA[lang_code]["fail"].format(ton_amount=ton_displayed))

def check_blockchain_subscription(target_comment, ton_needed):
    required_nanotons = int(ton_needed * 1_000_000_000)
    url = f"https://toncenter.com/api/v2/getTransactions?address={MY_TON_WALLET}&limit=40"
    try:
        response = requests.get(url).json()
        if response.get("ok"):
            current_time = int(time.time())
            for tx in response["result"]:
                if tx.get("in_msg", {}).get("message") == target_comment:
                    value_nanotons = int(tx.get("in_msg", {}).get("value", "0"))
                    tx_time = int(tx.get("utime", 0))
                    
                    if value_nanotons >= required_nanotons and (current_time - tx_time) < 2592000:
                        return True
    except Exception:
        pass
    return False

def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
