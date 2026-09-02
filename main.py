import os
import asyncio
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes

TOKEN = os.environ.get("8249620025:AAEhanZ3z2eC3-dOd-eA6gj2Rj2iIkwhYgA")

subscriptions = {}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    new_member = result.new_chat_member
    
    if new_member.status in ["member", "administrator"]:
        user_id = new_member.user.id
        chat_id = update.effective_chat.id
        days_to_add = 30
        expire_date = datetime.now() + timedelta(days=days_to_add)
        
        subscriptions[user_id] = {
            "chat_id": chat_id,
            "expire_at": expire_date
        }

async def add_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        chat_id = update.effective_chat.id
        expire_date = datetime.now() + timedelta(days=days)
        subscriptions[user_id] = {
            "chat_id": chat_id,
            "expire_at": expire_date
        }
        await update.message.reply_text(f"تم تحديد اشتراك {user_id} لمدة {days} يوم.")
    except Exception:
        await update.message.reply_text("الاستخدام: /add [user_id] [days]")

async def check_expirations(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    to_remove = []

    for user_id, info in list(subscriptions.items()):
        if now >= info["expire_at"]:
            chat_id = info["chat_id"]
            
            # طرد العضو وإلغاء الحظر مباشرة دون إرسال رسائل
            try:
                await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
                to_remove.append(user_id)
                print(f"تم طرد العضو {user_id} لانتهاء الاشتراك.")
            except Exception as e:
                print(f"خطأ في طرد العضو {user_id}: {e}")

    for user_id in to_remove:
        del subscriptions[user_id]

def main():
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("add", add_subscription))

    job_queue = app.job_queue
    job_queue.run_repeating(check_expirations, interval=60, first=10)

    print("البوت يعمل على السحابة...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
