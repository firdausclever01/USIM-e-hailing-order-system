import asyncio
import threading
import os
from flask import Flask, request, jsonify
from telethon import TelegramClient, events

api_id = 34569406
api_hash = 'f9b8a66dc67f43bea1cc5502689c0f33'
TARGET_GROUP_ID = -1001307640388

app = Flask(__name__)
live_orders_queue = []

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram E-Hailing Dispatcher</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">
    <header class="bg-slate-900 border-b border-slate-800 py-4 px-6 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-xl">🚗</div>
            <div>
                <h1 class="text-base font-bold text-white">Cloud E-Hailing Dispatcher</h1>
                <p class="text-xs text-emerald-400">● 24/7 Cloud Active</p>
            </div>
        </div>
    </header>
    <main class="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col space-y-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl flex-1">
            <h3 class="text-sm font-bold text-white mb-3">📥 Live Customer Orders</h3>
            <div id="orders-container" class="space-y-3">
                <div class="text-center py-12 text-slate-500">Connecting to cloud stream...</div>
            </div>
        </div>
    </main>
    <script>
        async function fetchLiveOrders() {
            try {
                const res = await fetch('/api/live-orders');
                const data = await res.json();
                const container = document.getElementById('orders-container');
                if (data && data.length > 0) {
                    container.innerHTML = data.map(order => `
                        <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-2 shadow-lg">
                            <div class="flex justify-between items-center">
                                <span class="text-xs font-semibold text-cyan-300">${order.sender} ${order.username ? '(@' + order.username + ')' : ''}</span>
                            </div>
                            <p class="text-xs text-slate-200 bg-slate-900 p-2 rounded font-mono">"${order.text}"</p>
                            <a href="${order.username ? 'https://t.me/' + order.username + '?text=' + encodeURIComponent('Hi, nak ambil ride ni ke? 🚗💨') : 'tg://'}" target="_blank" class="bg-sky-600 hover:bg-sky-500 text-white font-bold py-2 px-3 rounded-lg text-xs text-center">
                                💬 Direct PM Customer
                            </a>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="text-center py-12 text-slate-500">Listening for incoming Telegram orders...</div>';
                }
            } catch (e) { console.error(e); }
        }
        setInterval(fetchLiveOrders, 3000);
        fetchLiveOrders();
    </script>
</body>
</html>"""

@app.route('/')
def index():
    return DASHBOARD_HTML

@app.route('/api/live-orders', methods=['GET'])
def get_live_orders():
    return jsonify(live_orders_queue)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        live_orders_queue.insert(0, data)
    return jsonify({"status": "success"}), 200

# --- TELEGRAM BACKGROUND WORKER ---
def start_telegram_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient('session_cloud', api_id, api_hash)

    @client.on(events.NewMessage(chats=TARGET_GROUP_ID))
    async def tele_handler(event):
        msg_text = event.raw_text
        sender = await event.get_sender()
        payload = {
            "sender": getattr(sender, 'first_name', 'Student'),
            "username": getattr(sender, 'username', None),
            "text": msg_text
        }
        import requests as http_req
        try:
            port = os.environ.get('PORT', 5000)
            http_req.post(f'http://127.0.0.1:{port}/webhook', json=payload, timeout=2)
        except Exception as e:
            print(f"Error: {e}")

    client.start()
    loop.run_until_complete(client.run_until_disconnected())

if not any(t.name == 'TelegramWorker' for t in threading.enumerate()):
    t = threading.Thread(target=start_telegram_listener, name='TelegramWorker', daemon=True)
    t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
