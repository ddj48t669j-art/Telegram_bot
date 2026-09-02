import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes

# ضع توكن البوت الخاص بك من BotFather هنا
TOKEN = "8249620025:AAEhanZ3z2eC3-dOd-eA6gj2Rj2iIkwhYgA"

subscriptions = {}

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    new_member = result.new_chat_member
    
    if new_member.status in ["member", "administrator"]:
        user_id = new_member.user.id
        chat_id = update.effective_chat.id
        
        # المدة الافتراضية عند الانضمام: 30 يوماً
        days_to_add = 30
        expire_date = datetime.now() + timedelta(days=days_to_add)
        
        subscriptions[user_id] = {
            "chat_id": chat_id,
            "expire_at": expire_date
        }
        print(f"تم تسجيل العضو {user_id} لمدة {days_to_add} يوم.")

async def add_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # استخدام الأمر داخل القناة/المجموعة: /add 123456789 7
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        chat_id = update.effective_chat.id
        
        expire_date = datetime.now() + timedelta(days=days)
        subscriptions[user_id] = {
            "chat_id": chat_id,
            "expire_at": expire_date
        }
        await update.message.reply_text(f"تم تحديد اشتراك المستخدم {user_id} لمدة {days} يوم.")
    except Exception:
        await update.message.reply_text("طريقة الاستخدام: /add [user_id] [عدد_الأيام]")

async def check_expirations(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    to_remove = []

    for user_id, info in list(subscriptions.items()):
        if now >= info["expire_at"]:
            try:
                # طرد العضو ثم إلغاء الحظر حتى يمكنه الانضمام مجدداً عند التجديد
                await context.bot.ban_chat_member(chat_id=info["chat_id"], user_id=user_id)
                await context.bot.unban_chat_member(chat_id=info["chat_id"], user_id=user_id)
                to_remove.append(user_id)
                print(f"تم طرد العضو {user_id} لانتهاء الاشتراك.")
            except Exception as e:
                print(f"خطأ في طرد العضو {user_id}: {e}")

    for user_id in to_remove:
        del subscriptions[user_id]

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("add", add_subscription))

    # فحص المنتهية صلاحيتهم كل 60 ثانية
    job_queue = app.job_queue
    job_queue.run_repeating(check_expirations, interval=60, first=10)

    print("البوت يعمل الآن...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

