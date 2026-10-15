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
    <title>Velocity Dispatch | Cloud E-Hailing</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen flex flex-col selection:bg-cyan-500 selection:text-white">
    <!-- Top Header -->
    <header class="bg-white/80 backdrop-blur-md border-b border-slate-200 py-4 px-6 sm:px-8 flex justify-between items-center sticky top-0 z-50 shadow-sm">
        <div class="flex items-center space-x-3.5">
            <div class="w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20 text-xl font-bold">
                ⚡
            </div>
            <div>
                <h1 class="text-base font-bold tracking-tight text-slate-900 flex items-center gap-2">
                    Velocity Dispatch <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-600 border border-cyan-200">v3.0 Light</span>
                </h1>
                <div class="flex items-center gap-2 mt-0.5">
                    <span class="relative flex h-2 w-2">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span class="text-xs text-emerald-600 font-medium">Synchronized with Telegram Cloud</span>
                </div>
            </div>
        </div>
        <div class="flex items-center gap-3">
            <div class="hidden sm:flex items-center bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-xl text-xs font-medium text-slate-600">
                Active Orders: <span id="count-num" class="text-cyan-600 font-bold ml-1.5">0</span>
            </div>
            <button onclick="fetchLiveOrders()" class="bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold px-4 py-2 rounded-xl border border-slate-200 shadow-sm transition-all duration-200 active:scale-95 flex items-center gap-1.5">
                <span>🔄</span> Refresh
            </button>
        </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 max-w-3xl w-full mx-auto p-4 sm:p-6 flex flex-col space-y-4">
        <div class="bg-white border border-slate-200/80 rounded-3xl p-5 sm:p-6 shadow-xl shadow-slate-200/50 flex-1 flex flex-col">
            <div class="flex justify-between items-center mb-4 pb-3 border-b border-slate-100">
                <h3 class="text-sm font-bold text-slate-800 tracking-wide uppercase flex items-center gap-2">
                    <span>📥</span> Live Customer Dispatch Stream
                </h3>
                <span class="text-xs text-slate-400">Auto-polling every 5s</span>
            </div>
            
            <div id="orders-container" class="space-y-3.5 flex-1">
                <div class="text-center py-16 text-slate-400 flex flex-col items-center justify-center space-y-3">
                    <div class="w-8 h-8 border-2 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin"></div>
                    <p class="text-xs font-medium">Establishing secure stream...</p>
                </div>
            </div>
        </div>
    </main>

    <!-- Scripting & Logic -->
    <script>
        async function fetchLiveOrders() {
            try {
                const res = await fetch('/api/live-orders');
                const data = await res.json();
                const container = document.getElementById('orders-container');
                const countBadge = document.getElementById('count-num');
                
                if (data.error) {
                    container.innerHTML = `<div class="text-center py-8 text-rose-600 font-mono text-xs bg-rose-50 p-4 rounded-2xl border border-rose-200">⚠️ Backend Error: ${data.error}</div>`;
                    return;
                }

                if (data && data.length > 0) {
                    countBadge.innerText = data.length;
                    container.innerHTML = data.map(order => {
                        const rideMsg = encodeURIComponent('Assalam, masih kosong? saya pickup boleh ya? 🚗💨');
                        
                        let chatLink = "";
                        if (order.username) {
                            chatLink = `https://t.me/${order.username}?text=${rideMsg}`;
                        } else {
                            // Using Telegram share bridge with prefilled text and deep link user targeting
                            chatLink = `https://t.me/share/url?url=${encodeURIComponent('tg://openmessage?user_id=' + order.sender_id)}&text=${rideMsg}`;
                        }

                        let userBadge = order.username 
                            ? `<span class="bg-cyan-50 text-cyan-600 border border-cyan-200 px-2.5 py-0.5 rounded-full text-[11px] font-semibold">@${order.username}</span>`
                            : `<span class="bg-amber-50 text-amber-600 border border-amber-200 px-2.5 py-0.5 rounded-full text-[11px] font-semibold">No Username</span>`;

                        return `
                            <div class="p-4 sm:p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-slate-300 transition-all duration-200 flex flex-col gap-3 shadow-sm hover:shadow-md">
                                <div class="flex justify-between items-center">
                                    <div class="flex items-center gap-2">
                                        <div class="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-xs text-slate-700 font-bold border border-slate-200">
                                            ${order.sender.charAt(0).toUpperCase()}
                                        </div>
                                        <span class="text-xs font-bold text-slate-800 tracking-wide">${order.sender}</span>
                                    </div>
                                    ${userBadge}
                                </div>
                                
                                <div class="bg-slate-50 px-3.5 py-2.5 rounded-xl border border-slate-100 text-xs font-mono text-slate-700 tracking-wide">
                                    "${order.text}"
                                </div>
                                
                                <a href="${chatLink}" target="_blank" class="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold py-2.5 px-4 rounded-xl text-xs text-center shadow-md shadow-cyan-600/20 transition-all duration-200 active:scale-[0.99] flex items-center justify-center gap-2">
                                    <span>💬</span> Direct PM Customer
                                </a>
                            </div>
                        `;
                    }).join('');
                } else {
                    countBadge.innerText = 0;
                    container.innerHTML = '<div class="text-center py-16 text-slate-400 text-xs font-medium">No recent orders found in the group stream.</div>';
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
    session_str = os.environ.get('SESSION_STRING', '')
    if not session_str:
        return jsonify({"error": "SESSION_STRING missing in environment variables"})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def fetch_orders_async():
        client = TelegramClient(StringSession(session_str), api_id, api_hash)
        await client.connect()
        try:
            if not await client.is_user_authorized():
                return {"error": "Telegram session unauthorized"}
            
            target_entity = await client.get_entity(TARGET_GROUP_ID)
            orders = []
            async for message in client.iter_messages(target_entity, limit=15):
                if message.text:
                    sender = await message.get_sender()
                    orders.append({
                        "msg_id": message.id,
                        "sender": getattr(sender, 'first_name', 'Student') if sender else 'Student',
                        "username": getattr(sender, 'username', None) if sender else None,
                        "sender_id": str(getattr(sender, 'id', '')) if sender else '',
                        "text": message.text
                    })
            return orders
        finally:
            await client.disconnect()

    try:
        result = loop.run_until_complete(fetch_orders_async())
        if isinstance(result, dict) and "error" in result:
            return jsonify(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        loop.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
