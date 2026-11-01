import json
import os
import requests
import urllib.parse
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = "9018579736:AAFbUfg0YIRZnWGlEBAfw8qUC1w1xuuXbN4"
SUPABASE_URL = "https://uhchxpzsnjcjddggqosh.supabase.co"
SUPABASE_KEY = "sb_publishable_KtMIJ4h3tDuEF_p4c_7VIg_iViLfBQf"
TELEGRAM_USERNAME = "BestMonero"
SITE_URL = "https://monero-store.vercel.app"

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

def get_products():
    url = f"{SUPABASE_URL}/rest/v1/products?select=*&qty=gt.0"
    headers = {
        'apikey': SUPABASE_KEY, 
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"SUPABASE ERROR: {response.status_code} - {response.text}")
            return []
        return response.json()
    except Exception as e:
        print(f"FETCH ERROR: {e}")
        return []

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Webhook is active!")
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update = json.loads(post_data.decode('utf-8'))

        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")

            if text == "/start":
                kb = {
                    "inline_keyboard": [
                        [{"text": "🛒 Наличие аккаунтов", "callback_data": "accounts"}],
                        [{"text": "⭐ Купить звезды", "callback_data": "stars_menu"}],
                        [{"text": "📖 Инструкция", "callback_data": "instruction"}],
                        [{"text": "🌐 Наш сайт", "url": SITE_URL}]
                    ]
                }
                send_message(chat_id, "👋 Добро пожаловать в **Monero Store**!\n\nВыберите действие:", kb)

        elif "callback_query" in update:
            callback_id = update["callback_query"]["id"]
            chat_id = update["callback_query"]["message"]["chat"]["id"]
            message_id = update["callback_query"]["message"]["message_id"]
            data = update["callback_query"]["data"]

            # Отвечаем телеграму, чтобы убрать часики на кнопке
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
            req = urllib.request.Request(url, data=json.dumps({"callback_query_id": callback_id}).encode('utf-8'), headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req)

            if data == "instruction":
                text = (
                    "📖 **Инструкция по покупке аккаунтов:**\n\n"
                    "Сайт не имеет функции оплаты аккаунтов прямо на нем, для оплаты телеграмм аккаунтов вы должны написать мне в личные сообщения и сказать какой аккаунт вы хотите купить.\n\n"
                    "**Оплата может происходить:**\n"
                    "• Рублями\n"
                    "• USDT\n"
                    "• Телеграмм звездами\n\n"
                    "При получении аккаунта заходить с впном данной страны, которой вы купили аккаунт. Советую вам отлежаться пару дней и не трогать его, чтоб телеграмм не выдал вам спамблок, за спамблок я не ручаюсь.\n\n"
                    "Приятных покупок!"
                )
                kb = {"inline_keyboard": [[{"text": "⬅️ Назад в меню", "callback_data": "main_menu"}]]}
                # Используем editMessageText, чтобы не спамить новыми сообщениями
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown", "reply_markup": kb}
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req)

            elif data == "accounts":
                products = get_products()
                if not products:
                    text = "😔 Товаров в наличии нет."
                    kb = {"inline_keyboard": [[{"text": "⬅️ Назад в меню", "callback_data": "main_menu"}]]}
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": kb}
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                    urllib.request.urlopen(req)
                else:
                    send_message(chat_id, "🛒 **Аккаунты в наличии:**")
                    for p in products:
                        text = f"✈️ **{p['flag']} {p['country']} {p['code']}**\n\n📝 {p['short_desc']}\n💰 Цена: {p['price']}\n📦 В наличии: {p['qty']} шт."
                        msg = f"Привет! Хочу купить аккаунт {p['flag']} {p['country']} {p['code']}.\nСсылка на товар: {SITE_URL}/?item={p['id']}"
                        buy_url = f"https://t.me/{TELEGRAM_USERNAME}?text={urllib.parse.quote(msg)}"
                        kb = {"inline_keyboard": [[{"text": "🛍 Купить", "url": buy_url}]]}
                        send_message(chat_id, text, kb)
                    
                    kb = {"inline_keyboard": [[{"text": "⬅️ Назад в меню", "callback_data": "main_menu"}]]}
                    send_message(chat_id, "Выберите действие:", kb)

            elif data == "stars_menu":
                text = "⭐ **Курс Monero Store**\n1.5 RUB = 1 Звезда\n\nВыберите количество звезд:"
                kb = {"inline_keyboard": []}
                for amount in [50, 100, 200, 300, 400, 500, 1000]:
                    kb["inline_keyboard"].append([{"text": f"{amount} звезд", "callback_data": f"buy_stars_{amount}"}])
                kb["inline_keyboard"].append([{"text": "⬅️ Назад в меню", "callback_data": "main_menu"}])
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown", "reply_markup": kb}
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req)

            elif data.startswith("buy_stars_"):
                amount = int(data.split("_")[2])
                price = amount * 1.5
                text = f"Отлично! С вас **{price} рублей** за {amount} звезд.\n\nНажмите кнопку ниже, чтобы связаться с продавцом:"
                msg = f"Привет! Хочу купить у тебя {amount} звезд!"
                buy_url = f"https://t.me/{TELEGRAM_USERNAME}?text={urllib.parse.quote(msg)}"
                kb = {"inline_keyboard": [[{"text": "💬 Написать продавцу", "url": buy_url}], [{"text": "⬅️ Назад", "callback_data": "stars_menu"}]]}
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown", "reply_markup": kb}
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req)

            elif data == "main_menu":
                kb = {
                    "inline_keyboard": [
                        [{"text": "🛒 Наличие аккаунтов", "callback_data": "accounts"}],
                        [{"text": "⭐ Купить звезды", "callback_data": "stars_menu"}],
                        [{"text": "📖 Инструкция", "callback_data": "instruction"}],
                        [{"text": "🌐 Наш сайт", "url": SITE_URL}]
                    ]
                }
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                payload = {"chat_id": chat_id, "message_id": message_id, "text": "👋 Главное меню **Monero Store**\nВыберите действие:", "parse_mode": "Markdown", "reply_markup": kb}
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")