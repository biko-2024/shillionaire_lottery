import telebot
from telebot import types
import random
from datetime import datetime

# ===== CONFIG =====
BOT_TOKEN = "8061689354:AAGdBzLjVBEpt9mLPiaeSM2Mu06AwpBi7rs"
ADMIN_CHAT_ID = 1790327982  # Your Telegram ID
ADMIN_USERNAME = "@bikila2022"  # Your Telegram username
PAYMENT_NUMBER = "+251912345678"  # Your Telebirr number
PAYMENT_NUMBER2 = "+251713115368"  # Your Telebirr number
ACCOUNT_NUMBER = "1000496832877"  # Your account number
TICKET_PRICE = 10  # ETB
ADMIN_COMMISSION = 0.10  # 10%

bot = telebot.TeleBot(BOT_TOKEN)

# Temporary storage
pending_verifications = {}
approved_tickets = []
winners_history = []  # Changed from last_winner to winners_history list

# ===== KEYBOARDS =====
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "🎟 Buy Ticket (10 ETB)",
        "🏆 Last Winner",
        "📋 List Buyers",
        "ℹ️ How It Works",
        "📞 Contact Admin"
    ]
    markup.add(*buttons)
    return markup

# ===== CORE FLOW =====
@bot.message_handler(commands=['start'])
def start(message):
    welcome_msg = (
        f"🎲 Welcome to shillionaire (ሺሊነር) Lottery Bot 🎲\n"
        f"💰 Daily Prize is changing every day but check in the group\n"
        f"⏰ Draw Time is changing every day but check in the group\n\n"
        f"group link: https://t.me/shillionaire_lottery\n\n"
        f"👇 Tap a button below to get started!"
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🎟 Buy Ticket (10 ETB)")
def request_payment(message):
    payment_instructions = (
        f"💵 Payment Instructions:\n"
        f"1. Send 10 ETB to {PAYMENT_NUMBER} via Telebirr\n"
        f"2. send 10 ETB TO {PAYMENT_NUMBER} via CBEBirr\n"
        f"3. send 10 ETB TO {PAYMENT_NUMBER2} via M-PESA| Safaricom\n"
        f"4. Send 10 ETB to {ACCOUNT_NUMBER} via bank account\n"
        f"5. send screenshot of the payment for verification Telebirr, CBEBirr, M-PESA\n"
        f"6. send transaction id of the payment for verification bank account\n"
        f"⚠️ Make sure the screenshot shows:\n"
        f"- Amount\n"
        f"- Recipient number\n"
        f"- Transaction time\n\n"
        f"Alternatively, you can send your transaction ID instead of a screenshot."
    )
    
    msg = bot.send_message(message.chat.id, payment_instructions)
    bot.register_next_step_handler(msg, handle_payment_proof)

def handle_payment_proof(message):
    ticket_num = f"TKT-{random.randint(1000, 9999)}"
    
    # Get username or create a fallback
    username = message.from_user.username
    if not username:
        username = f"User_{message.chat.id}"
    
    # Check if message is a photo or text (transaction ID)
    if message.photo:
        # Handle photo proof
        proof_id = message.photo[-1].file_id
        proof_type = "screenshot"
        
        pending_verifications[message.chat.id] = {
            "name": message.from_user.first_name,
            "username": username,
            "user_id": message.chat.id,
            "ticket": ticket_num,
            "proof_id": proof_id,
            "proof_type": proof_type,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # Forward to admin with action buttons
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.chat.id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.chat.id}")
        )
        
        # Fix the caption formatting to avoid Markdown parsing errors
        caption = (
            f"🆕 Payment Verification\n\n"
            f"👤 User: {message.from_user.first_name}\n"
            f"🔗 Username: @{username}\n"
            f"🆔 ID: {message.chat.id}\n"
            f"🎟 Ticket: {ticket_num}\n"
            f"⏰ Time: {pending_verifications[message.chat.id]['time']}"
        )
        
        bot.send_photo(
            ADMIN_CHAT_ID,
            proof_id,
            caption=caption,
            reply_markup=markup
        )
        
    elif message.text:
        # Handle transaction ID
        transaction_id = message.text.strip()
        proof_type = "transaction_id"
        
        pending_verifications[message.chat.id] = {
            "name": message.from_user.first_name,
            "username": username,
            "user_id": message.chat.id,
            "ticket": ticket_num,
            "transaction_id": transaction_id,
            "proof_type": proof_type,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # Forward to admin with action buttons
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.chat.id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.chat.id}")
        )
        
        # Message for admin
        admin_message = (
            f"🆕 Payment Verification\n\n"
            f"👤 User: {message.from_user.first_name}\n"
            f"🔗 Username: @{username}\n"
            f"🆔 ID: {message.chat.id}\n"
            f"🎟 Ticket: {ticket_num}\n"
            f"💳 Transaction ID: {transaction_id}\n"
            f"⏰ Time: {pending_verifications[message.chat.id]['time']}"
        )
        
        bot.send_message(
            ADMIN_CHAT_ID,
            admin_message,
            reply_markup=markup
        )
        
    else:
        bot.send_message(message.chat.id, "❌ Please send a valid screenshot or transaction ID!")
        return
    
    bot.send_message(
        message.chat.id,
        f"⏳ Your payment is under review\n"
        f"🎫 Temporary Ticket: {ticket_num}\n\n"
        "We'll notify you once approved!\n"
        f" IF YOU HAVE ANY QUESTIONS, CONTACT ADMIN {ADMIN_USERNAME}\n"
    )

# ===== ADMIN CONTROLS =====
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_admin_decision(call):
    try:
        user_id = int(call.data.split('_')[1])
        
        if user_id not in pending_verifications:
            try:
                bot.answer_callback_query(call.id, "❌ Verification expired")
            except telebot.apihelper.ApiTelegramException as e:
                # Handle expired callback query
                if "query is too old" in str(e):
                    # Just log the error and continue
                    print(f"Callback query expired: {e}")
                else:
                    # Re-raise other API exceptions
                    raise
            return
        
        ticket_data = pending_verifications[user_id]
        
        if call.data.startswith('approve_'):
            approved_tickets.append(ticket_data)
            
            # Send approval message without Markdown
            approval_message = (
                f"✅ Payment Approved!\n\n"
                f"🎫 Official Ticket: {ticket_data['ticket']}\n"
                f"💰 Prize is changing every day but check in the group\n"
                f"⏰ Draw Time is changing every day but check in the group\n\n"
                f"Good luck! 🍀"
            )
            
            bot.send_message(user_id, approval_message)
            
            # Update message based on whether it's a photo or text
            if ticket_data['proof_type'] == 'screenshot':
                # For photos, update the caption
                new_caption = f"✅ APPROVED\n\n{call.message.caption}"
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=new_caption
                )
            else:
                # For text messages, edit the message text
                new_text = f"✅ APPROVED\n\n{call.message.text}"
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=new_text
                )
            
        else:  # Rejection
            # Send rejection message without Markdown
            rejection_message = (
                f"❌ Payment Rejected\n\n"
                f"Possible reasons:\n"
                f"- Unclear screenshot\n"
                f"- Wrong payment amount\n"
                f"- Missing transaction details\n\n"
                f"Please try again with a clear screenshot showing:\n"
                f"1. Payment amount (10 ETB)\n"
                f"2. Recipient number\n"
                f"3. Transaction time\n\n"
                f"Send new screenshot when ready."
            )
            
            bot.send_message(user_id, rejection_message)
            
            # Update message based on whether it's a photo or text
            if ticket_data['proof_type'] == 'screenshot':
                # For photos, update the caption
                new_caption = f"❌ REJECTED\n\n{call.message.caption}"
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=new_caption
                )
            else:
                # For text messages, edit the message text
                new_text = f"❌ REJECTED\n\n{call.message.text}"
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=new_text
                )
        
        del pending_verifications[user_id]
        
        try:
            bot.answer_callback_query(call.id)
        except telebot.apihelper.ApiTelegramException as e:
            # Handle expired callback query
            if "query is too old" in str(e):
                # Just log the error and continue
                print(f"Callback query expired: {e}")
            else:
                # Re-raise other API exceptions
                raise
                
    except Exception as e:
        print(f"Error in handle_admin_decision: {e}")
        # Try to answer the callback query if possible
        try:
            bot.answer_callback_query(call.id, "❌ An error occurred")
        except:
            pass

@bot.message_handler(commands=['list'], func=lambda m: m.chat.id == ADMIN_CHAT_ID)
def list_tickets(message):
    if not approved_tickets:
        bot.send_message(ADMIN_CHAT_ID, "❌ No tickets sold yet!")
        return
    
    total_tickets = len(approved_tickets)
    total_revenue = total_tickets * TICKET_PRICE
    admin_commission = total_revenue * ADMIN_COMMISSION
    prize_pool = total_revenue - admin_commission
    
    ticket_list = "📋 Current Ticket Buyers:\n\n"
    for ticket in approved_tickets:
        ticket_list += f"👤 @{ticket['username']}\n"
    
    ticket_list += f"""
💰 Summary:
• Total Buyers: {total_tickets}
• Total Revenue: {total_revenue} ETB
• Admin Commission (10%): {admin_commission} ETB
• Prize Pool: {prize_pool} ETB
"""
    
    bot.send_message(ADMIN_CHAT_ID, ticket_list)

@bot.message_handler(commands=['draw'], func=lambda m: m.chat.id == ADMIN_CHAT_ID)
def conduct_draw(message):
    if not approved_tickets:
        bot.send_message(ADMIN_CHAT_ID, "❌ No approved tickets to draw from")
        return
    
    # Get list of unique usernames
    usernames = list(set(ticket['username'] for ticket in approved_tickets))
    
    # Randomly select a winner from usernames
    winner_username = random.choice(usernames)
    
    # Find all tickets belonging to the winner
    winner_tickets = [t for t in approved_tickets if t['username'] == winner_username]
    
    # Select one random ticket from winner's tickets
    winner = random.choice(winner_tickets)
    
    # Calculate prize pool and commission
    total_tickets = len(approved_tickets)
    total_revenue = total_tickets * TICKET_PRICE
    admin_commission = total_revenue * ADMIN_COMMISSION
    prize_pool = total_revenue - admin_commission
    
    # First notify admin
    admin_message = (
        f"🏆 LOTTERY DRAW COMPLETE\n\n"
        f"👤 Winner: @{winner['username']}\n"
        f"🎟 Ticket: {winner['ticket']}\n"
        f"💰 Prize Pool: {prize_pool} ETB\n"
        f"💵 Admin Commission: {admin_commission} ETB\n"
        f"📅 Draw Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    
    bot.send_message(ADMIN_CHAT_ID, admin_message)
    
    # Send announcement to all ticket buyers
    for ticket in approved_tickets:
        # Create personalized message for each user
        is_winner = ticket['user_id'] == winner['user_id']
        
        if is_winner:
            # Special message for the winner
            winner_message = (
                f"🎉 CONGRATULATIONS! YOU ARE THE WINNER! 🎉\n\n"
                f"🏆 LOTTERY DRAW COMPLETE\n"
                f"👤 Your Username: @{winner['username']}\n"
                f"🎟 Your Winning Ticket: {winner['ticket']}\n"
                f"💰 Your Prize: {prize_pool} ETB\n"
                f"⏰ Draw Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Please contact {ADMIN_USERNAME} to claim your prize!"
            )
            
            bot.send_message(ticket['user_id'], winner_message)
        else:
            # Message for non-winners
            message_text = (
                f"🏆 LOTTERY DRAW COMPLETE 🏆\n\n"
                f"👤 Winner: @{winner['username']}\n"
                f"🎟 Winning Ticket: {winner['ticket']}\n"
                f"💰 Prize: {prize_pool} ETB\n"
                f"⏰ Draw Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Better luck next time! 🍀"
            )
            
            bot.send_message(ticket['user_id'], message_text)
    
    # Add winner to history
    global winners_history
    winner['draw_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    winner['prize_amount'] = prize_pool
    winners_history.insert(0, winner)  # Add to the beginning of the list
    
    # Keep only the last 10 winners to avoid the list getting too long
    if len(winners_history) > 10:
        winners_history = winners_history[:10]
    
    # Clear for next draw
    approved_tickets.clear()
    
    # Send confirmation to admin
    bot.send_message(ADMIN_CHAT_ID, "✅ Draw completed and announcements sent to all ticket buyers!")

# ===== USER FEATURES =====
@bot.message_handler(func=lambda m: m.text == "🏆 Last Winner")
def show_last_winner(message):
    if not winners_history:
        bot.send_message(message.chat.id, "No winners drawn yet!")
        return
    
    # Create a message with all winners
    winners_message = "🏆 LOTTERY WINNERS HISTORY 🏆\n\n"
    
    for i, winner in enumerate(winners_history):
        winners_message += (
            f"#{i+1}. Winner: @{winner['username']}\n"
            f"   Ticket: {winner['ticket']}\n"
            f"   Prize: {winner['prize_amount']} ETB\n"
            f"   Date: {winner['draw_time']}\n\n"
        )
    
    winners_message += f"Next draw today at 8 PM!"
    
    bot.send_message(message.chat.id, winners_message)

@bot.message_handler(func=lambda m: m.text == "📞 Contact Admin")
def contact_admin(message):
    contact_message = (
        f"✉️ Need help?\n\n"
        f"Contact our admin directly:\n"
        f"{ADMIN_USERNAME}\n\n"
        f"We're happy to assist you!"
    )
    
    bot.send_message(message.chat.id, contact_message)

@bot.message_handler(func=lambda m: m.text == "ℹ️ How It Works")
def how_it_works(message):
    instructions = (
        f"📢 How to Play:\n\n"
        f"1. Tap '🎟 Buy Ticket'\n"
        f"2. Reply with payment screenshot or transaction id\n"
        f"3. Wait for admin approval\n"
        f"4. Check draw results in the group\n\n"
        f"5. In list buyers, you can see the list of buyers and the total number of buyers\n"
        f"6. In last winner, you can see the list of winners and the total number of winners\n"
        f"7. In how it works, you can see the instructions on how to play\n"
        f"8. In contact admin, you can contact the admin directly\n"
        f"9. group link: https://t.me/shillionaire_lottery\n"
        f"10. In group link, you can join the group to see the draw time and the prize\n"
        f"🏆 Prize Structure:\n" 
        f" if 20 people buy ticket, the prize is 10*10*90% = 90 ETB\n"
        f" if 100 people buy ticket, the prize is 100*10*90% = 900 ETB\n"
        f" if 200 people buy ticket, the prize is 200*10*90% = 1800 ETB\n"
        f" when the draw time come, the system will draw and announce the winner in the group and anouncement is sent to all buyers\n"
        f" even if you are not winner, you can try again tomorrow\n"
        f"the system is fair and transparent, the admin does not have any control over the draw\n"
        f"the admin will not know your username or id, so you can be sure that the draw is fair and transparent\n"
        f"the draw is done by math random\n"
        f"so if you are lucky, you can be the winner\n"
        f" Winners contacted directly\n\n"
        f"❓ Questions? Contact {ADMIN_USERNAME}"
    )
    
    bot.send_message(message.chat.id, instructions)

@bot.message_handler(func=lambda m: m.text == "📋 List Buyers")
def show_buyers_list(message):
    if not approved_tickets:
        bot.send_message(message.chat.id, "❌ No tickets sold yet!")
        return
    
    total_tickets = len(approved_tickets)
    
    buyers_list = "📋 Current Ticket Buyers:\n\n"
    for ticket in approved_tickets:
        buyers_list += f"👤 @{ticket['username']}\n"
    
    buyers_list += f"\n💰 Total Buyers: {total_tickets}"
    
    bot.send_message(message.chat.id, buyers_list)

# ===== RUN BOT =====
if __name__ == "__main__":
    print("🤖 Lottery Bot is running...")
    bot.polling()