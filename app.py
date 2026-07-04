import telebot
import requests
import os
import threading
import time
from flask import Flask
import psycopg2  # Handles serverless database connections

# --- ⚠️ CONFIGURATION ⚠️ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")  # 👈 Add your Neon Connection String in Render Config
COMMUNITY_ID = -1002241567123  
MY_TON_WALLET = "UQA3n4Lgs0gJRinUW-CFbwOpILhmkUvVT-dsoXKjgMhJiGR-"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- TRANSLATION DICTIONARY ---
LANG_DATA = {
    "en": {
        "name": "English 🇬🇧",
        "text": "💰 *Monthly Subscription Fee: 50 EUR*\n\n*Your dynamic amount to send right now:* `{ton_amount:.2f} TON`\n\n*TON Wallet Address:*\n`{wallet}`\n\n⚠️ *IMPORTANT:* You must copy and paste the code below into the **Comment / Memo** field of your transaction, or the bot cannot track your payment:\n`{comment}`\n\n❌ *WE ONLY ACCEPT TON*.\n\nTap the verification button below as soon as your wallet says sent!",
        "verify_btn": "🔄 Verify My Subscription",
        "success": "✅ Subscription Confirmed! Tap this link to join: {link}",
        "fail": "❌ Active subscription not detected. Ensure you sent at least {ton_amount:.2f} TON with the exact comment code and try again."
    },
    "sr": {
        "name": "Srpski 🇷🇸",
        "text": "💰 *Mesečna pretplata: 50 EUR*\n\n*Tačan iznos za slanje sada:* `{ton_amount:.2f} TON`\n\n*Adresa TON novčanika:*\n`{wallet}`\n\n⚠️ *VAŽNO:* Morate kopirati i nalepiti kod ispod u polje **Komentar / Memo** prilikom slanja transakcije, u suprotnom bot neće moći da potvrdi uplatu:\n`{comment}`\n\n❌ *PRIHVATAMO SAMO TON*.\n\nKliknite na dugme ispod čim vaš novčanik prikaže da je poslato!",
        "verify_btn": "🔄 Potvrdi moju pretplatu",
        "success": "✅ Pretplata potvrđena! Kliknite na ovaj link da se pridružite: {link}",
        "fail": "❌ Aktivna pretplata nije pronađena. Proverite da li ste poslali najmanje {ton_amount:.2f} TON sa tačnim komentarom i pokušajte ponovo."
    },
    "mk": {
        "name": "Македонски 🇲🇰",
        "text": "💰 *Месечна претплата: 50 EUR*\n\n*Точен износ за испраќање сега:* `{ton_amount:.2f} TON`\n\n*Адреса на TON паричник:*\n`{wallet}`\n\n⚠️ *ВАЖНО:* Мора да го копирате и залепите кодот подолу во полето **Коментар / Memo** при плаќањето, во спротивно ботот нема да ја препознае уплатата:\n`{comment}`\n\n❌ *ПРИФАЌАМЕ ИСКЛУЧИВО TON*.\n\nПритиснете го копчето подолу штом вашиот паричник покаже дека е испратено!",
        "verify_btn": "🔄 Потврди ја мојата претплата",
        "success": "✅ Претплата е потврдена! Кликнете на овој линк за да се приклучите: {link}",
        "fail": "❌ Активна претплата не е пронајдена. Проверете дали сте испратиле најмалку {ton_amount:.2f} TON со точниот коментар и обидете се повторно."
    },
    "sq": {
        "name": "Shqip 🇦🇱",
        "text": "💰 *Abonimi Mujor: 50 EUR*\n\n*Shuma e saktë për të dërguar tani:* `{ton_amount:.2f} TON`\n\n*Adresa e Portofolit TON:*\n`{wallet}`\n\n⚠️ *E RËNDËSISHME:* Duhet të kopjoni dhe ngjitni kodin e mëposhtëm në fushën **Comment / Memo** të transaksionit tuaj, përndryshe boti nuk mund ta gjurmojë pagesën:\n`{comment}`\n\n❌ *PRANOJMË VETËM TON*.\n\nShtypni butonin e mëposhtëm sapo portofoli juaj të thotë u dërgua!",
        "verify_btn": "🔄 Verifiko Abonimin Tim",
        "success": "✅ Abonimi u konfirmua! Klikoni këtë link për t'u bashkuar: {link}",
        "fail": "❌ Abonimi aktiv nuk u gjet. Sigurohuni qe keni dërguar të paktën {ton_amount:.2f} TON met kodin e saktë dhe provoni përsëri."
    }
}

# --- DATABASE SETUP ---
def init_db():
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    user_id BIGINT PRIMARY KEY,
                    expiry_time BIGINT
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Database table validated successfully.")
        except Exception as e:
            print(f"Database Initialization Error: {e}")

def save_member_subscription(user_id, days=30):
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            expiry_timestamp = int(time.time()) + (days * 86400)
            cur.execute("""
                INSERT INTO members (user_id, expiry_time) 
                VALUES (%s, %s) 
                ON CONFLICT (user_id) 
                DO UPDATE SET expiry_time = EXCLUDED.expiry_time
            """, (user_id, expiry_timestamp))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error saving membership details: {e}")

# --- BACKGROUND AUTOMATED EVICTION LOOP ---
def auto_eviction_worker():
    while True:
        if DATABASE_URL:
            try:
                conn = psycopg2.connect(DATABASE_URL)
                cur = conn.cursor()
                current_timestamp = int(time.time())
                
                # Fetch members whose timestamp is in the past
                cur.execute("SELECT user_id FROM members WHERE expiry_time < %s", (current_timestamp,))
                expired_users = cur.fetchall()
                
                for row in expired_users:
                    u_id = row[0]
                    try:
                        # Ban physically kicks them out of the group
                        bot.ban_chat_member(COMMUNITY_ID, u_id)
                        # Immediate unban clears their restriction status so they can pay to rejoin later
                        bot.unban_chat_member(COMMUNITY_ID, u_id)
                        
                        # Remove record from database tracking
                        cur.execute("DELETE FROM members WHERE user_id = %s", (u_id,))
                        conn.commit()
                        print(f"Success: Automatically removed expired user ID {u_id}")
                    except Exception as kick_error:
                        print(f"Could not remove member {u_id} (Check bot permissions): {kick_error}")
                        
                cur.close()
                conn.close()
            except Exception as db_loop_error:
                print(f"Eviction Engine Loop Error: {db_loop_error}")
        
        time.sleep(3600)  # Runs check automatically every 1 hour

def get_required_ton():
    try:
        url = "https://min-api.cryptocompare.com/data/price?fsym=TON&tsyms=EUR"
        res = requests.get(url).json()
        return 50.0 / res.get("EUR", 5.50)
    except Exception:
        return 9.50  # Balanced fallback if currency endpoint times out

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
    ton_needed = get_required_ton()
    
    formatted_text = LANG_DATA[lang_code]["text"].format(
        ton_amount=ton_needed,
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
    
    ton_needed = get_required_ton()
    
    if check_blockchain_subscription(expected_memo, ton_needed):
        # 1. Update/Add registration expiration timeline in database
        save_member_subscription(int(user_id), days=30)
        
        # 2. Grant single-use access credentials
        try:
            invite = bot.create_chat_invite_link(chat_id=COMMUNITY_ID, member_limit=1)
            bot.send_message(call.message.chat.id, LANG_DATA[lang_code]["success"].format(link=invite.invite_link))
        except Exception:
            bot.send_message(call.message.chat.id, "Setup Alert: Ensure the bot is added as an Administrator with Ban Users rights!")
    else:
        bot.send_message(call.message.chat.id, LANG_DATA[lang_code]["fail"].format(ton_amount=ton_needed))

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

# Start systems
init_db()
threading.Thread(target=auto_eviction_worker, daemon=True).start()
threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
