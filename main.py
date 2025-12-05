import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler

from config import BOT_TOKEN, ADMIN_ID
from database import add_user, get_user, delete_user, list_users, is_user_expired
from xray_manager import generate_uuid, add_vmess_user, remove_vmess_user, get_vmess_users
from utils import generate_vmess_link, format_user_info
from monitor import get_active_connections, get_connection_count

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Disable httpx verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Conversation states
DELETE_EMAIL = range(1)

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
        [InlineKeyboardButton("📊 Monitor", callback_data="monitor")],
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
        "/monitor - Show active connections\n"
        "/info <username> - Get account info\n"
        "/help - Show help"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

@admin_only
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "create":
        await create_start(update, context)
    elif query.data == "list":
        await list_users_command(update, context)
    elif query.data == "delete":
        await delete_start(update, context)
    elif query.data == "monitor":
        await monitor_command(update, context)
    elif query.data == "help":
        await help_command(update, context)
    elif query.data.startswith("days_"):
        await create_user_with_days(update, context)

@admin_only
async def create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start create user - show duration buttons"""
    keyboard = [
        [InlineKeyboardButton("1 Day", callback_data="days_1"),
         InlineKeyboardButton("3 Days", callback_data="days_3")],
        [InlineKeyboardButton("7 Days", callback_data="days_7"),
         InlineKeyboardButton("30 Days", callback_data="days_30")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = "⏳ *Select Account Duration:*\n\nChoose how long this VMess account should be valid:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")

async def create_user_with_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create user with selected days"""
    query = update.callback_query
    await query.answer()
    
    # Extract days from callback data
    days = int(query.data.split('_')[1])
    
    # Generate username (vmess_timestamp)
    import time
    username = f"vmess_{int(time.time())}"
    
    # Generate UUID
    uuid = generate_uuid()
    
    # Add to XRay
    success, message = add_vmess_user(username, uuid)
    if not success:
        await query.edit_message_text(f"❌ Failed to add user to XRay: {message}")
        return
    
    # Add to database
    user = add_user(username, uuid, days)
    
    # Generate VMess link
    vmess_link = generate_vmess_link(username, uuid)
    
    # Format response
    response = (
        "✅ *VMess Account Created Successfully!*\n\n"
        f"{format_user_info(user, uuid)}\n"
        f"🔗 *VMess Link:*\n`{vmess_link}`\n\n"
        "Copy the link above and import it to your V2Ray client."
    )
    
    await query.edit_message_text(response, parse_mode="Markdown")

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
        for username, user in users.items():
            expired = is_user_expired(username)
            status = "❌ Expired" if expired else "✅ Active"
            text += f"• `{username}` - {status}\n"
            text += f"  Expires: {user['expiry_date']}\n\n"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

@admin_only
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start delete user conversation"""
    message_text = (
        "🗑 Please send the username of the user to delete:\n\n"
        "Send /cancel to abort."
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message_text)
    else:
        await update.message.reply_text(message_text)
    return DELETE_EMAIL

async def delete_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive username and delete user"""
    username = update.message.text.strip()
    
    # Check if user exists
    user = get_user(username)
    if not user:
        await update.message.reply_text("❌ User not found!")
        return ConversationHandler.END
    
    # Remove from XRay
    success, message = remove_vmess_user(username)
    if not success:
        await update.message.reply_text(f"❌ Failed to remove from XRay: {message}")
        return ConversationHandler.END
    
    # Remove from database
    delete_user(username)
    
    await update.message.reply_text(f"✅ User `{username}` has been deleted successfully!", parse_mode="Markdown")
    return ConversationHandler.END

@admin_only
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user info"""
    if not context.args:
        await update.message.reply_text("Usage: /info <username>")
        return
    
    username = context.args[0]
    user = get_user(username)
    
    if not user:
        await update.message.reply_text("❌ User not found!")
        return
    
    # Generate VMess link
    vmess_link = generate_vmess_link(username, user['uuid'])
    
    # Check expiry
    expired = is_user_expired(username)
    status = "❌ Expired" if expired else "✅ Active"
    
    response = (
        f"ℹ️ *User Information*\n\n"
        f"{format_user_info(user, user['uuid'])}"
        f"📊 Status: {status}\n\n"
        f"🔗 *VMess Link:*\n`{vmess_link}`"
    )
    
    await update.message.reply_text(response, parse_mode="Markdown")

@admin_only
async def monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active connections monitor"""
    try:
        # Get connection count
        conn_count = get_connection_count()
        
        # Get active connections
        connections = get_active_connections()
        
        if conn_count == 0 and not connections:
            text = "📊 *Connection Monitor*\n\n🔴 No active connections"
        else:
            text = f"📊 *Connection Monitor*\n\n"
            text += f"🟢 *Active Connections: {conn_count}*\n\n"
            
            if connections:
                text += "*Connection Details:*\n"
                for i, conn in enumerate(connections, 1):
                    if 'user' in conn:
                        text += f"{i}. User: `{conn['user']}`\n"
                        text += f"   ⬆️ Up: {conn['upload']} | ⬇️ Down: {conn['download']}\n"
                        text += f"   📊 Total: {conn['total']}\n\n"
                    elif 'ip' in conn:
                        text += f"{i}. IP: `{conn['ip']}` - {conn['status']}\n\n"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        error_text = f"❌ Error getting monitor data: {str(e)}"
        if update.callback_query:
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)

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
        "/monitor - Monitor active connections\n"
        "/info <username> - Get account info and link\n"
        "/help - Show this help message\n\n"
        "*How to use:*\n"
        "1. Use /create to create a new account\n"
        "2. Select validity period (1/3/7/30 days)\n"
        "3. Copy the VMess link and import to your client\n"
        "4. Use /list to see all accounts\n"
        "5. Use /delete to remove accounts\n\n"
        "*Note:* VMess links use your VPS IP address directly (non-TLS)."
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(help_text, parse_mode="Markdown")

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create conversation handler for delete only
    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            DELETE_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_username)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_start))
    application.add_handler(delete_conv_handler)
    application.add_handler(CommandHandler("list", list_users_command))
    application.add_handler(CommandHandler("monitor", monitor_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
