import telebot
from telebot import types
import json
import random
import os

# ==========================================
# CONFIGURATION SECTION
# ==========================================

TOKEN = '8545700007:AAH4DfjClxyKaO0-VEYX1XlgJKYfuv4JBQ0'

# Add as many Monetag Direct Links as you want here
AD_LINKS = [
    "https://url-shortener.me/7CN",
    "https://url-shortener.me/7CZ",
    "https://url-shortener.me/7D6"
]

# How much money a user gets per click (e.g., $0.01)
REWARD_PER_CLICK = 0.01

# Minimum amount required to withdraw
MIN_WITHDRAW = 5.00 

# File to save user balances
DATA_FILE = "users.json"

# ==========================================
# BOT SETUP
# ==========================================

bot = telebot.TeleBot(TOKEN)

# 1. Load Data Function
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

# 2. Save Data Function
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# 3. Helper to get user balance
def get_balance(user_id):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"balance": 0.0}
        save_data(data)
    return data[user_id]["balance"]

# 4. Helper to add money
def add_balance(user_id, amount):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"balance": 0.0}
    
    data[user_id]["balance"] += amount
    data[user_id]["balance"] = round(data[user_id]["balance"], 4) # Round to 4 decimals
    save_data(data)

# 5. Helper to deduct money (for withdrawals)
def deduct_balance(user_id, amount):
    data = load_data()
    user_id = str(user_id)
    if user_id in data and data[user_id]["balance"] >= amount:
        data[user_id]["balance"] -= amount
        data[user_id]["balance"] = round(data[user_id]["balance"], 4)
        save_data(data)
        return True
    return False

# ==========================================
# BOT COMMANDS
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Initialize user in database
    get_balance(message.from_user.id)
    
    # Create Main Menu Keyboard
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_earn = types.KeyboardButton("💰 Earn Money")
    btn_wallet = types.KeyboardButton("Vm Wallet")
    btn_withdraw = types.KeyboardButton("🏦 Withdraw")
    markup.add(btn_earn, btn_wallet, btn_withdraw)
    
    bot.reply_to(message, 
                 "Welcome to TheMorningStar! \n\n"
                 "Click 'Earn Money' to view ads and get rewards.\n"
                 "Check your 'Wallet' to see your balance.", 
                 reply_markup=markup)

# Handle "Earn Money" Button
@bot.message_handler(func=lambda message: message.text == "💰 Earn Money")
def earn_money(message):
    # Pick a random link
    random_link = random.choice(AD_LINKS)
    
    # Create Inline Keyboard with URL and a "Claim" button
    markup = types.InlineKeyboardMarkup()
    
    # Button 1: The Ad (URL)
    btn_ad = types.InlineKeyboardButton("🌟 Click to View Ad", url=random_link)
    
    # Button 2: Claim Reward (Callback)
    # Note: In a real strict bot, you'd verify the click via API, but for this simple version
    # the user manually clicks 'Claim' after viewing.
    btn_claim = types.InlineKeyboardButton("✅ I Have Viewed It", callback_data="claim_reward")
    
    markup.add(btn_ad)
    markup.add(btn_claim)
    
    bot.reply_to(message, "Click the link below, view the ad, then click 'I Have Viewed It' to get your reward!", reply_markup=markup)

# Handle "Claim" Button Click
@bot.callback_query_handler(func=lambda call: call.data == "claim_reward")
def callback_claim(call):
    # Add money
    add_balance(call.from_user.id, REWARD_PER_CLICK)
    
    # Delete the claim button so they can't click it twice
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    bot.send_message(call.message.chat.id, f"✅ Success! ${REWARD_PER_CLICK} added to your wallet.")

# Handle "Wallet" Button
@bot.message_handler(func=lambda message: message.text == "Vm Wallet")
def show_wallet(message):
    bal = get_balance(message.from_user.id)
    bot.reply_to(message, f"💳 **Your Wallet Balance:**\n\n💵 ${bal}")

# Handle "Withdraw" Button
@bot.message_handler(func=lambda message: message.text == "🏦 Withdraw")
def withdraw_request(message):
    bal = get_balance(message.from_user.id)
    
    if bal < MIN_WITHDRAW:
        bot.reply_to(message, f"❌ Insufficient funds.\n\nYour Balance: ${bal}\nMinimum Withdraw: ${MIN_WITHDRAW}")
    else:
        msg = bot.reply_to(message, f"💰 You have ${bal}.\n\nPlease enter your Wallet Address (e.g., USDT TRC20 or PayPal Email):")
        bot.register_next_step_handler(msg, process_withdrawal)

def process_withdrawal(message):
    wallet_address = message.text
    user_id = message.from_user.id
    bal = get_balance(user_id)
    
    if deduct_balance(user_id, bal):
        # Here is where you would integrate an automatic payout API if you had one.
        # For now, it simulates a request sent to the admin.
        
        bot.reply_to(message, "✅ Withdrawal Request Received!\n\n"
                              f"Amount: ${bal}\n"
                              f"Address: {wallet_address}\n\n"
                              "You will receive your funds within 24 hours.")
        
        print(f"NEW WITHDRAWAL: User {user_id} requested ${bal} to {wallet_address}")
    else:
        bot.reply_to(message, "❌ Error processing withdrawal. Check your balance.")

# Keep running
print("TheMorningStar Bot is running with Wallet System...")
bot.infinity_polling()