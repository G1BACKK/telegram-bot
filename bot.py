# bot.py

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
GROUP_ID = -10012345678  # Replace with your group ID
VIP_LINK = "https://t.me/yourvipgroup"  # Replace with your VIP group invite link

# SQLite database setup
conn = sqlite3.connect("user_shares.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, shares INTEGER)")
conn.commit()

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        user_id = member.id
        cursor.execute("INSERT OR IGNORE INTO users (user_id, shares) VALUES (?, 0)", (user_id,))
        conn.commit()

        keyboard = [
            [InlineKeyboardButton("🔗 SHARE GROUP (10 REQUIRED)", callback_data="share")],
            [InlineKeyboardButton("🚀 JOIN VIP (LOCKED)", callback_data="vip")]
        ]
        await update.message.reply_text(
            f"👋 Welcome [{member.first_name}](tg://user?id={user_id})!\n\n"
            "⚠️ *VIP ACCESS LOCKED*\n\n"
            "📢 Share this group with 10 friends to unlock VIP:\n"
            "👉 https://t.me/yourgroup\n\n"
            "👇 Click SHARE GROUP to begin!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def track_shares(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.forward_from_chat and update.message.forward_from_chat.id == GROUP_ID:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, shares) VALUES (?, 0)", (user_id,))
        cursor.execute("UPDATE users SET shares = shares + 1 WHERE user_id = ?", (user_id,))
        conn.commit()

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    cursor.execute("SELECT shares FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    shares = result[0] if result else 0

    if query.data == "share":
        await query.answer()
        await query.edit_message_text(
            "📤 *SHARE THIS LINK 10 TIMES:*\n\n"
            "👉 https://t.me/yourgroup\n\n"
            "After sharing, click ✅ DONE SHARING below.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ DONE SHARING", callback_data="check")]
            ])
        )
    elif query.data == "check":
        if shares >= 10:
            await query.answer("🎉 VIP UNLOCKED!", show_alert=True)
            await query.edit_message_text(
                f"✅ *ACCESS GRANTED!*\n\n"
                f"🚀 Join VIP Group: [Click Here]({VIP_LINK})",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            await query.answer(f"❌ Need {10 - shares} more shares!", show_alert=True)
    elif query.data == "vip":
        await query.answer("🔒 Complete sharing first!", show_alert=True)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_shares))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()

if __name__ == "__main__":
    main()
