import os
import asyncio
from flask import Flask, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = 34569406
api_hash = 'f9b8a66dc67f43bea1cc5502689c0f33'
TARGET_GROUP_ID = -1001307640388

app = Flask(__name__)

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
                <p id="connection-status" class="text-xs text-emerald-400">● Live & Connected</p>
            </div>
        </div>
        <button onclick="fetchLiveOrders()" class="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-1.5 rounded-lg border border-slate-700">🔄 Refresh</button>
    </header>
    <main class="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col space-y-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl flex-1">
            <h3 class="text-sm font-bold text-white mb-3">📥 Live Customer Orders</h3>
            <div id="orders-container" class="space-y-3">
                <div class="text-center py-12 text-slate-500">Loading orders from Telegram...</div>
            </div>
        </div>
    </main>
    <script>
        async function fetchLiveOrders() {
            try {
                const res = await fetch('/api/live-orders');
                const data = await res.json();
                const container = document.getElementById('orders-container');
                
                if (data.error) {
                    container.innerHTML = `<div class="text-center py-6 text-rose-400 font-mono text-xs bg-rose-950/30 p-4 rounded-xl border border-rose-900">⚠️ Backend Error: ${data.error}</div>`;
                    return;
                }

                if (data && data.length > 0) {
                    container.innerHTML = data.map(order => {
                        // Use username link if available, otherwise fallback to tg://user?id=
                        let chatLink = order.username 
                            ? `https://t.me/${order.username}?text=${encodeURIComponent('Hi, nak ambil ride ni ke? 🚗💨')}`
                            : `tg://user?id=${order.sender_id}`;

                        return `
                            <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-2 shadow-lg">
                                <div class="flex justify-between items-center">
                                    <span class="text-xs font-semibold text-cyan-300">${order.sender} ${order.username ? '(@' + order.username + ')' : '(No Username)'}</span>
                                </div>
                                <p class="text-xs text-slate-200 bg-slate-900 p-2 rounded font-mono">"${order.text}"</p>
                                <a href="${chatLink}" target="_blank" class="bg-sky-600 hover:bg-sky-500 text-white font-bold py-2 px-3 rounded-lg text-xs text-center">
                                    💬 Direct PM Customer
                                </a>
                            </div>
                        `;
                    }).join('');
                } else {
                    container.innerHTML = '<div class="text-center py-12 text-slate-500">No recent orders found in group.</div>';
                }
            } catch (e) { console.error(e); }
        }
        setInterval(fetchLiveOrders, 5000);
        fetchLiveOrders();
    </script>
</body>
</html>"""

@app.route('/')
def index():
    return DASHBOARD_HTML

@app.route('/api/live-orders', methods=['GET'])
def get_live_orders():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def fetch_messages():
        session_str = os.environ.get('SESSION_STRING', '')
        if not session_str:
            return {"error": "SESSION_STRING environment variable is missing on Render!"}
            
        client = TelegramClient(StringSession(session_str), api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                return {"error": "Session string is unauthorized or invalid!"}
            
            target_entity = None
            async for dialog in client.iter_dialogs():
                if dialog.id == TARGET_GROUP_ID or dialog.id == abs(TARGET_GROUP_ID):
                    target_entity = dialog.entity
                    break
            
            if not target_entity:
                target_entity = await client.get_entity(TARGET_GROUP_ID)

            orders = []
            async for message in client.iter_messages(target_entity, limit=15):
                if message.text:
                    sender = await message.get_sender()
                    orders.append({
                        "msg_id": message.id,
                        "sender": getattr(sender, 'first_name', 'Student') if sender else 'Student',
                        "username": getattr(sender, 'username', None) if sender else None,
                        "sender_id": getattr(sender, 'id', '') if sender else '',
                        "text": message.text
                    })
            return orders
        except Exception as e:
            return {"error": str(e)}
        finally:
            await client.disconnect()

    result = loop.run_until_complete(fetch_messages())
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
