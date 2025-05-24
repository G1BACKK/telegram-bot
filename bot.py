import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Config
TOKEN = "7602201949:AAG8E2YSvOUrw0J5RRTG0cXlyxjvW5hEKZY"
GROUP_ID = -1002316637165
PINNED_MSG_ID = 87
VIP_LINK = "https://t.me/+q1Wg9YeCAKFlOGRl"

# DB Setup
conn = sqlite3.connect("forwards.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, forwards INTEGER DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS forward_receivers (user_id INTEGER, receiver_id INTEGER, UNIQUE(user_id, receiver_id))")
conn.commit()

# Welcome and Instructions
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        user_id = member.id
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

        keyboard = [
            [InlineKeyboardButton("🔁 FORWARD GROUP PINNED MESSAGE", url=f"https://t.me/c/2316637165/{PINNED_MSG_ID}")],
            [InlineKeyboardButton("✅ DONE SHARING", callback_data="check")],
            [InlineKeyboardButton("🚀 VIP ACCESS (LOCKED)", callback_data="vip")]
        ]

        await update.effective_chat.send_message(
            text=(
                f"👋 Welcome [{member.first_name}](tg://user?id={user_id})!\n\n"
                "📌 *Forward the pinned message to 3 friends to unlock VIP access!*\n"
                "1. Tap the forward button\n"
                "2. Send to 3 different users\n"
                "3. Tap ✅ DONE SHARING",
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Forward Tracker
async def track_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg: Message = update.message
    user_id = msg.forward_sender_name or msg.forward_from_chat or msg.forward_from
    sender_id = msg.from_user.id

    if msg.forward_from_chat and msg.forward_from_chat.id == GROUP_ID and msg.forward_from_message_id == PINNED_MSG_ID:
        receiver_id = msg.chat.id
        cursor.execute("SELECT 1 FROM forward_receivers WHERE user_id = ? AND receiver_id = ?", (sender_id, receiver_id))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO forward_receivers (user_id, receiver_id) VALUES (?, ?)", (sender_id, receiver_id))
            cursor.execute("UPDATE users SET forwards = forwards + 1 WHERE user_id = ?", (sender_id,))
            conn.commit()

# Button Handler
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    cursor.execute("SELECT forwards FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    count = result[0] if result else 0

    if query.data == "check":
        if count >= 3:
            await query.edit_message_text(
                text=f"✅ ACCESS GRANTED!\n\n🎉 [Join VIP Channel Here]({VIP_LINK})",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            await query.answer(f"❌ You need {3 - count} more forwards!", show_alert=True)
    elif query.data == "vip":
        await query.answer("🔒 You must forward to 3 users first!", show_alert=True)

# Main Bot
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT & (~filters.COMMAND), track_forward))
    app.run_polling()

if __name__ == "__main__":
    main()

