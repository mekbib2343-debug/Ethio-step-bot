import os
import telebot
import time
import hashlib
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# ==================== FLASK SERVER (KEEP-ALIVE) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <body style="background: #000; color: #fff; text-align: center; padding: 50px;">
            <h1>✅ EthioStep Finance Bot</h1>
            <p>Status: <strong>LIVE on Render 24/7</strong></p>
            <p>Telegram: @EthioStepFinanceBot</p>
            <p>💎 Investment Platform</p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

def run_flask():
    app.run(host='0.0.0.0', port=10000)

Thread(target=run_flask, daemon=True).start()
print("🌐 Flask server started on port 10000")

# ==================== DATABASE SIMULATION ====================
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    print("❌ ERROR: BOT_TOKEN not set in Render Environment Variables!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
print(f"✅ Bot token loaded: {TOKEN[:10]}...")

# In-memory database (in production, use real database)
users_db = {}
agents_db = {}
managers_db = {}
investments_db = {}
referrals_db = {}
vip_queue = []

# ==================== PAYMENT DETAILS ====================
PAYMENT_DETAILS = {
    'cbe_bank': {
        'account': '1000601221911',
        'name': 'ETHIOSTEP FINANCE',
        'bank': 'COMMERCIAL BANK OF ETHIOPIA'
    },
    'cbebirr': {
        'number': '0974284385',
        'name': 'ETHIOSTEP FINANCE'
    },
    'telebirr': {
        'number': '0974284385',
        'name': 'ETHIOSTEP FINANCE'
    },
    'mpesa': {
        'number': '0708873603',
        'name': 'ETHIOSTEP FINANCE'
    },
    'usdt': {
        'address': 'TKsaxnjL7X7X1P6t7VrK7qHwL8nZ9X8mNk',
        'network': 'TRC-20'
    }
}

# ==================== INVESTMENT PLANS ====================
INVESTMENT_PLANS = {
    '1': {'name': 'STARTER', 'amount': 20, 'return': 80, 'days': 10},
    '2': {'name': 'PREMIUM', 'amount': 50, 'return': 100, 'days': 10},
    '3': {'name': 'GOLD', 'amount': 100, 'return': 200, 'days': 10},
    'vip': {'name': 'VIP', 'amount': 1000, 'return': 5000, 'days': 10}
}

# ==================== HELPER FUNCTIONS ====================
def generate_referral_code(user_id):
    return f"REF{user_id}{hashlib.md5(str(user_id).encode()).hexdigest()[:4]}"

def generate_agent_id(user_id):
    return f"AGT{user_id}{hashlib.md5(str(user_id).encode()).hexdigest()[:4]}"

def generate_manager_id(user_id):
    return f"MGR{user_id}{hashlib.md5(str(user_id).encode()).hexdigest()[:4]}"

def calculate_daily_vip_earnings():
    # Last VIP in queue gets 70% daily
    if vip_queue:
        last_vip = vip_queue[-1]
        return last_vip['amount'] * 0.70
    return 0

# ==================== BOT COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    user_id = user.id
    
    # Check if user exists
    if user_id not in users_db:
        users_db[user_id] = {
            'id': user_id,
            'name': user.first_name,
            'username': user.username,
            'phone': None,
            'balance': 0.0,
            'total_invested': 0.0,
            'total_earned': 0.0,
            'referral_code': generate_referral_code(user_id),
            'referrals': [],
            'referral_earnings': 0.0,
            'is_agent': False,
            'is_manager': False,
            'agent_id': None,
            'manager_id': None,
            'vip_level': 0,
            'joined_date': datetime.now().isoformat(),
            'selected_plan': None
        }
        
        # Check for referral from link
        if len(message.text.split()) > 1:
            ref_code = message.text.split()[1]
            # Find user with this referral code
            for uid, data in users_db.items():
                if data['referral_code'] == ref_code and uid != user_id:
                    # Add referral relationship
                    users_db[uid]['referrals'].append(user_id)
                    users_db[uid]['referral_earnings'] += 10  # $10 bonus for referral
                    users_db[user_id]['agent_id'] = uid
                    break
    
    user_data = users_db[user_id]
    
    # Welcome message with interactive buttons
    welcome = f"""
👑 *WELCOME {user.first_name}!*

🏦 **ETHIOSTEP FINANCE PLATFORM**
*Smart Investment | Fixed Returns | Daily Earnings*

💰 *YOUR WALLET*
Balance: ${user_data['balance']:.2f}
Total Invested: ${user_data['total_invested']:.2f}
Total Earned: ${user_data['total_earned']:.2f}

📊 *QUICK ACTIONS:*
1️⃣ /invest - Invest Money
2️⃣ /deposit - Add Funds
3️⃣ /withdraw - Withdraw Earnings
4️⃣ /referral - Refer & Earn
5️⃣ /agent - Agent System
6️⃣ /vip - VIP Program
7️⃣ /wallet - My Wallet
8️⃣ /support - 24/7 Support

🔗 *Your Referral Code:* `{user_data['referral_code']}`
👥 Referrals: {len(user_data['referrals'])} users
💸 Referral Earnings: ${user_data['referral_earnings']:.2f}

💎 *Start with $20 → Get $80 in 10 Days!*"""
    
    # Create inline keyboard
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("💰 INVEST NOW", callback_data='invest_menu'),
        telebot.types.InlineKeyboardButton("💳 DEPOSIT", callback_data='deposit_menu'),
        telebot.types.InlineKeyboardButton("👥 REFER & EARN", callback_data='referral_menu'),
        telebot.types.InlineKeyboardButton("🤝 BECOME AGENT", callback_data='agent_menu'),
        telebot.types.InlineKeyboardButton("👑 VIP PROGRAM", callback_data='vip_menu'),
        telebot.types.InlineKeyboardButton("📞 SUPPORT", url='https://t.me/EthioStepSupport')
    )
    
    bot.send_message(message.chat.id, welcome, 
                    parse_mode='Markdown', 
                    reply_markup=keyboard)
    
    print(f"✅ User {user_id} started bot")

# ==================== DEPOSIT COMMAND ====================
@bot.message_handler(commands=['deposit'])
def deposit_command(message):
    user_id = message.from_user.id
    
    deposit_text = f"""
💳 *DEPOSIT FUNDS*

*Choose Payment Method:*

🇪🇹 *ETHIOPIAN PAYMENT:*
🏦 *CBE BANK*
Account: `{PAYMENT_DETAILS['cbe_bank']['account']}`
Name: {PAYMENT_DETAILS['cbe_bank']['name']}
Bank: {PAYMENT_DETAILS['cbe_bank']['bank']}

📱 *CBE BIRR*
Number: `{PAYMENT_DETAILS['cbebirr']['number']}`
Name: {PAYMENT_DETAILS['cbebirr']['name']}

📱 *TELEBIRR*
Number: `{PAYMENT_DETAILS['telebirr']['number']}`
Name: {PAYMENT_DETAILS['telebirr']['name']}

📱 *M-PESA (Kenya)*
Number: `{PAYMENT_DETAILS['mpesa']['number']}`
Name: {PAYMENT_DETAILS['mpesa']['name']}

🌍 *INTERNATIONAL (USDT)*
💎 *USDT TRC-20*
Address: `{PAYMENT_DETAILS['usdt']['address']}`
Network: {PAYMENT_DETAILS['usdt']['network']}

⚠️ *IMPORTANT INSTRUCTIONS:*
1. Send EXACT amount for your chosen plan
2. Take CLEAR screenshot of payment
3. Forward screenshot here
4. Include your name in message
5. Wait for admin confirmation (15-30 min)

✅ *Your investment activates immediately after confirmation!*

📝 *After payment, send screenshot here...*"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("📸 SEND SCREENSHOT", callback_data='send_screenshot'),
        telebot.types.InlineKeyboardButton("💎 VIEW PLANS", callback_data='invest_menu'),
        telebot.types.InlineKeyboardButton("📞 CONTACT ADMIN", url='https://t.me/EthioStepAdmin')
    )
    
    bot.send_message(message.chat.id, deposit_text, 
                    parse_mode='Markdown', 
                    reply_markup=keyboard)

# ==================== HANDLE SCREENSHOTS ====================
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Thank user and notify admin
    bot.reply_to(message, f"""
✅ *SCREENSHOT RECEIVED!*

Thank you {user_name}!

📋 *Payment Details Received:*
• User: {user_name}
• User ID: {user_id}
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⏳ *Status:* Under Review
⏰ *Processing:* 15-30 minutes

📞 *Admin will contact you soon for confirmation.*
💬 *Stay connected!*""", parse_mode='Markdown')
    
    # Notify admin (change to your admin ID)
    admin_id = 123456789  # CHANGE TO YOUR ADMIN ID
    try:
        bot.forward_message(admin_id, message.chat.id, message.message_id)
        bot.send_message(admin_id, f"📸 New payment screenshot from @{message.from_user.username} (ID: {user_id})")
    except:
        print(f"⚠️ Could not notify admin about screenshot from {user_id}")

# ==================== REFERRAL SYSTEM ====================
@bot.message_handler(commands=['referral'])
def referral_command(message):
    user_id = message.from_user.id
    user_data = users_db.get(user_id, {})
    
    ref_code = user_data.get('referral_code', generate_referral_code(user_id))
    ref_link = f"https://t.me/EthioStepFinanceBot?start={ref_code}"
    
    referral_text = f"""
👥 *REFERRAL PROGRAM*

💰 *EARN $10 FOR EACH FRIEND!*

🔗 *Your Referral Link:*
`{ref_link}`

📋 *Your Referral Code:*
`{ref_code}`

📊 *YOUR STATS:*
• Total Referrals: {len(user_data.get('referrals', []))}
• Referral Earnings: ${user_data.get('referral_earnings', 0):.2f}
• Pending Bonus: $0.00

🎯 *HOW IT WORKS:*
1. Share your link with friends
2. Friend clicks link & registers
3. Friend makes first investment
4. You get $10 instantly!

💵 *REFERRAL BONUS STRUCTURE:*
• Level 1: $10 per referral
• Level 2: $5 (when your referral refers someone)
• Level 3: $2 (second level referrals)

📈 *BECOME AGENT:* /agent
*(Earn 20% commission from your team)*"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("📤 SHARE LINK", switch_inline_query=f"Join EthioStep Finance! {ref_link}"),
        telebot.types.InlineKeyboardButton("🤝 BECOME AGENT", callback_data='agent_menu'),
        telebot.types.InlineKeyboardButton("💼 MY TEAM", callback_data='my_team')
    )
    
    bot.send_message(message.chat.id, referral_text, 
                    parse_mode='Markdown', 
                    reply_markup=keyboard)

# ==================== AGENT SYSTEM ====================
@bot.message_handler(commands=['agent'])
def agent_command(message):
    user_id = message.from_user.id
    user_data = users_db.get(user_id, {})
    
    if not user_data.get('is_agent'):
        # Show agent enrollment
        agent_text = f"""
🤝 *AGENT PROGRAM*

💰 *EARN 20% COMMISSION FROM YOUR TEAM!*

🎯 *AGENT BENEFITS:*
• 20% commission from direct referrals
• 10% from level 2 referrals
• 5% from level 3 referrals
• Daily bonus for active agents
• Manager promotion opportunity

📊 *AGENT REQUIREMENTS:*
1. Minimum 5 direct referrals
2. $500 total team investment
3. Active for 30 days

💵 *MANAGER PROGRAM:*
When you enroll last VIP, you become MANAGER
• Get 70% daily from last VIP's investment
• Manage team of agents
• Higher commission rates

💰 *UPGRADE TO AGENT:*
Send $50 registration fee to become agent

📝 *To become Agent, contact Admin:* @EthioStepAdmin"""
    else:
        # Show agent dashboard
        agent_id = user_data.get('agent_id', generate_agent_id(user_id))
        agent_text = f"""
👨‍💼 *AGENT DASHBOARD*

🆔 Agent ID: `{agent_id}`
⭐ Level: {'MANAGER' if user_data.get('is_manager') else 'AGENT'}

💰 *EARNINGS:*
• Today: $0.00
• This Week: $0.00
• Total: ${user_data.get('agent_earnings', 0):.2f}

👥 *TEAM STATS:*
• Direct Team: 0 agents
• Total Team: 0 people
• Team Investment: $0.00

📈 *MANAGER BONUS:*
Last VIP Daily 70%: ${calculate_daily_vip_earnings():.2f}

🔗 *Your Agent Link:*
`https://t.me/EthioStepFinanceBot?start=agent_{agent_id}`"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("📊 MY TEAM", callback_data='agent_team'),
        telebot.types.InlineKeyboardButton("💰 WITHDRAW EARNINGS", callback_data='agent_withdraw'),
        telebot.types.InlineKeyboardButton("👑 ENROLL VIP", callback_data='enroll_vip'),
        telebot.types.InlineKeyboardButton("📞 CONTACT MANAGER", url='https://t.me/EthioStepAdmin')
    )
    
    bot.send_message(message.chat.id, agent_text, 
                    parse_mode='Markdown', 
                    reply_markup=keyboard)

# ==================== VIP PROGRAM ====================
@bot.message_handler(commands=['vip'])
def vip_command(message):
    vip_text = """
👑 *VIP PROGRAM*

💰 *INVEST $1000 → GET $5000 IN 10 DAYS!*

🎯 *VIP BENEFITS:*
• 500% return in 10 days
• Priority support
• Daily earnings for manager
• Special VIP status

⚡ *VIP DAILY EARNINGS SYSTEM:*
Last enrolled VIP earns 70% daily for their manager!

📊 *CURRENT VIP QUEUE:*
"""
    
    # Add VIP queue info
    if vip_queue:
        for i, vip in enumerate(vip_queue[-5:], 1):  # Show last 5 VIPs
            vip_text += f"{i}. VIP {vip['user_id']} - ${vip['amount']}\n"
        
        last_vip = vip_queue[-1]
        vip_text += f"\n💰 *LAST VIP DAILY EARNINGS:*\n"
        vip_text += f"Manager gets ${last_vip['amount'] * 0.7:.2f} daily!\n"
    else:
        vip_text += "No VIPs yet. Be the first!\n"
    
    vip_text += f"""
💎 *BECOME VIP:*
1. Invest $1000
2. Contact Admin
3. Get VIP status
4. Start earning

📞 *Contact Admin to become VIP:* @EthioStepAdmin"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("👑 BECOME VIP", callback_data='become_vip'),
        telebot.types.InlineKeyboardButton("🤝 ENROLL VIP", callback_data='enroll_vip'),
        telebot.types.InlineKeyboardButton("📊 VIP QUEUE", callback_data='vip_queue'),
        telebot.types.InlineKeyboardButton("📞 ADMIN", url='https://t.me/EthioStepAdmin')
    )
    
    bot.send_message(message.chat.id, vip_text, 
                    parse_mode='Markdown', 
                    reply_markup=keyboard)

# ==================== INVESTMENT PLANS ====================
@bot.message_handler(commands=['invest'])
def invest_command(message):
    invest_text = """
💰 *INVESTMENT PLANS*

🎯 *10-DAY FIXED RETURNS*

1️⃣ *STARTER PLAN*
• Invest: $20
• Returns: $80 after 10 days
• Profit: $60 (+300%)
• In ETB: 1,150 Birr

2️⃣ *PREMIUM PLAN*
• Invest: $50
• Returns: $100 after 10 days
• Profit: $50 (+100%)
• In ETB: 2,875 Birr

3️⃣ *GOLD PLAN*
• Invest: $100
• Returns: $200 after 10 days
• Profit: $100 (+100%)
• In ETB: 5,750 Birr

👑 *VIP PLAN*
• Invest: $1,000
• Returns: $5,000 after 10 days
• Profit: $4,000 (+400%)
• Special: Manager gets 70% daily

💱 *Exchange Rate:* 1 USDT = 57.5 ETB

📝 *HOW TO INVEST:*
1. Choose plan (reply 1, 2, 3, or VIP)
2. Use /deposit for payment
3. Send screenshot
4. Get confirmation
5. Start earning!"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("💰 PLAN 1 ($20)", callback_data='plan_1'),
        telebot.types.InlineKeyboardButton("💰 PLAN 2 ($50)", callback_data='plan_2'),
        telebot.types.InlineKeyboardButton("💰 PLAN 3 ($100)", callback_data='plan_3'),
        telebot.types.InlineKeyboardButton("👑 VIP ($1000)", callback_data='plan_vip'),
        telebot.types.InlineKeyboardButton("💳 DEPOSIT", callback_data='deposit_menu')
    )
    
    bot.send_message(message.chat.id, invest_text, 
                    parse_mode='Markdown', 
                    reply_markup=keyboard)

# ==================== BUTTON HANDLERS ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if call.data == 'invest_menu':
        invest_command(call.message)
    
    elif call.data == 'deposit_menu':
        deposit_command(call.message)
    
    elif call.data == 'referral_menu':
        referral_command(call.message)
    
    elif call.data == 'agent_menu':
        agent_command(call.message)
    
    elif call.data == 'vip_menu':
        vip_command(call.message)
    
    elif call.data == 'send_screenshot':
        bot.answer_callback_query(call.id, "📸 Please send your payment screenshot now!")
    
    elif call.data == 'become_vip':
        vip_text = """
👑 *TO BECOME VIP:*

1. Send $1000 to any payment method
2. Contact @EthioStepAdmin with screenshot
3. You will be added to VIP queue
4. Your manager earns 70% daily from your investment

💎 *VIP Benefits:*
• $5000 return in 10 days
• Priority support
• Special status

📞 *Contact Admin Now:* @EthioStepAdmin"""
        bot.send_message(call.message.chat.id, vip_text, parse_mode='Markdown')
    
    elif call.data == 'enroll_vip':
        enroll_text = """
🤝 *ENROLL VIP MEMBER*

As an Agent/Manager, you can enroll VIP members:

📋 *Requirements to Enroll VIP:*
1. You must be active Agent
2. VIP invests $1000
3. You get 70% daily from their investment

💰 *Your Daily Earnings:*
For each VIP you enroll: $700 daily for 10 days!

📝 *How to Enroll:*
1. Refer someone to invest $1000
2. They mention your Agent ID
3. Admin will connect you
4. You start earning daily

📞 *Contact Admin:* @EthioStepAdmin"""
        bot.send_message(call.message.chat.id, enroll_text, parse_mode='Markdown')
    
    elif call.data.startswith('plan_'):
        plan_map = {
            'plan_1': '1',
            'plan_2': '2', 
            'plan_3': '3',
            'plan_vip': 'vip'
        }
        
        plan_key = plan_map.get(call.data)
        if plan_key in INVESTMENT_PLANS:
            plan = INVESTMENT_PLANS[plan_key]
            etb = plan['amount'] * 57.5
            
            response = f"""
✅ *{plan['name']} PLAN SELECTED*

📋 *Details:*
• Investment: ${plan['amount']}
• In ETB: {etb:.0f} Birr
• Returns: ${plan['return']} after {plan['days']} days
• Profit: ${plan['return'] - plan['amount']}

💳 *Next Steps:*
1. Use /deposit for payment details
2. Make payment
3. Send screenshot
4. Get confirmation
5. Start earning!

📞 *Need help?* @EthioStepAdmin"""
            
            bot.send_message(call.message.chat.id, response, parse_mode='Markdown')
    
    bot.answer_callback_query(call.id)

# ==================== START BOT ====================
print("=" * 60)
print("🚀 ETHIOSTEP FINANCE BOT - COMPLETE SYSTEM")
print("🏠 Host: Render.com | 24/7 Operation")
print("💰 Features: Investment | Agent System | VIP Program")
print("👥 Referral System | Manager Earnings")
print("=" * 60)
print("🤖 Bot is starting...")

if __name__ == '__main__':
    while True:
        try:
            print(f"📡 [{datetime.now().strftime('%H:%M:%S')}] Polling for messages...")
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"⚠️ Error: {str(e)}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10)
