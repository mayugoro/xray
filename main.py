import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler

from config import BOT_TOKEN, ADMIN_ID
from database import add_user, get_user, delete_user, list_users, is_user_expired
from xray_manager import generate_uuid, add_vmess_user, remove_vmess_user, get_vmess_users
from utils import generate_vmess_link, format_user_info

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Disable httpx verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Conversation states
EMAIL, DAYS = range(2)

def admin_only(func):
    """Decorator to restrict commands to admin only"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        return await func(update, context)
    return wrapper

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show main menu"""
    keyboard = [
        [InlineKeyboardButton("➕ Create User", callback_data="create")],
        [InlineKeyboardButton("📋 List Users", callback_data="list")],
        [InlineKeyboardButton("🗑 Delete User", callback_data="delete")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🤖 *VMess Bot Manager*\n\n"
        "Welcome! Use the buttons below to manage VMess accounts.\n\n"
        "Available commands:\n"
        "/start - Show this menu\n"
        "/create - Create new VMess account\n"
        "/list - List all accounts\n"
        "/delete - Delete an account\n"
        "/info <email> - Get account info\n"
        "/help - Show help"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

@admin_only
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "create":
        await query.edit_message_text("Please send the email for the new user:")
        return EMAIL
    elif query.data == "list":
        await list_users_command(update, context)
    elif query.data == "delete":
        await query.edit_message_text("Please send the email of the user to delete:")
        return EMAIL
    elif query.data == "help":
        await help_command(update, context)

@admin_only
async def create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start create user conversation"""
    await update.message.reply_text(
        "📧 Please send the email for the new VMess user:\n"
        "(Example: user@example.com)\n\n"
        "Send /cancel to abort."
    )
    return EMAIL

async def create_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive email and ask for days"""
    email = update.message.text.strip()
    
    # Validate email format (basic)
    if '@' not in email or ' ' in email:
        await update.message.reply_text("❌ Invalid email format. Please send a valid email:")
        return EMAIL
    
    # Check if user already exists
    if get_user(email):
        await update.message.reply_text("❌ User already exists! Please use a different email:")
        return EMAIL
    
    context.user_data['email'] = email
    await update.message.reply_text(
        "⏳ How many days should this account be valid?\n"
        "(Example: 30)\n\n"
        "Send /cancel to abort."
    )
    return DAYS

async def create_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive days and create user"""
    try:
        days = int(update.message.text.strip())
        if days <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please send a positive number:")
        return DAYS
    
    email = context.user_data['email']
    
    # Generate UUID
    uuid = generate_uuid()
    
    # Add to XRay
    success, message = add_vmess_user(email, uuid)
    if not success:
        await update.message.reply_text(f"❌ Failed to add user to XRay: {message}")
        return ConversationHandler.END
    
    # Add to database
    user = add_user(email, uuid, days)
    
    # Generate VMess link
    vmess_link = generate_vmess_link(email, uuid)
    
    # Format response
    response = (
        "✅ *VMess Account Created Successfully!*\n\n"
        f"{format_user_info(user, uuid)}\n"
        f"🔗 *VMess Link:*\n`{vmess_link}`\n\n"
        "Copy the link above and import it to your V2Ray client."
    )
    
    await update.message.reply_text(response, parse_mode="Markdown")
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("❌ Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

@admin_only
async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users"""
    users = list_users()
    
    if not users:
        text = "📋 No users found."
    else:
        text = f"📋 *Total Users: {len(users)}*\n\n"
        for email, user in users.items():
            expired = is_user_expired(email)
            status = "❌ Expired" if expired else "✅ Active"
            text += f"• {email} - {status}\n"
            text += f"  Expires: {user['expiry_date']}\n\n"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

@admin_only
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start delete user conversation"""
    await update.message.reply_text(
        "🗑 Please send the email of the user to delete:\n\n"
        "Send /cancel to abort."
    )
    return EMAIL

async def delete_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive email and delete user"""
    email = update.message.text.strip()
    
    # Check if user exists
    user = get_user(email)
    if not user:
        await update.message.reply_text("❌ User not found!")
        return ConversationHandler.END
    
    # Remove from XRay
    success, message = remove_vmess_user(email)
    if not success:
        await update.message.reply_text(f"❌ Failed to remove from XRay: {message}")
        return ConversationHandler.END
    
    # Remove from database
    delete_user(email)
    
    await update.message.reply_text(f"✅ User `{email}` has been deleted successfully!", parse_mode="Markdown")
    return ConversationHandler.END

@admin_only
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user info"""
    if not context.args:
        await update.message.reply_text("Usage: /info <email>")
        return
    
    email = context.args[0]
    user = get_user(email)
    
    if not user:
        await update.message.reply_text("❌ User not found!")
        return
    
    # Generate VMess link
    vmess_link = generate_vmess_link(email, user['uuid'])
    
    # Check expiry
    expired = is_user_expired(email)
    status = "❌ Expired" if expired else "✅ Active"
    
    response = (
        f"ℹ️ *User Information*\n\n"
        f"{format_user_info(user, user['uuid'])}"
        f"📊 Status: {status}\n\n"
        f"🔗 *VMess Link:*\n`{vmess_link}`"
    )
    
    await update.message.reply_text(response, parse_mode="Markdown")

@admin_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = (
        "📚 *VMess Bot Help*\n\n"
        "*Available Commands:*\n"
        "/start - Show main menu\n"
        "/create - Create new VMess account\n"
        "/list - List all VMess accounts\n"
        "/delete - Delete a VMess account\n"
        "/info <email> - Get account info and link\n"
        "/help - Show this help message\n\n"
        "*How to use:*\n"
        "1. Use /create to create a new account\n"
        "2. Enter email and validity period\n"
        "3. Copy the VMess link and import to your client\n"
        "4. Use /list to see all accounts\n"
        "5. Use /delete to remove accounts\n\n"
        "*Note:* VMess links use your VPS IP address directly."
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(help_text, parse_mode="Markdown")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create conversation handler
    create_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("create", create_start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_email)],
            DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_days)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(create_conv_handler)
    application.add_handler(delete_conv_handler)
    application.add_handler(CommandHandler("list", list_users_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
