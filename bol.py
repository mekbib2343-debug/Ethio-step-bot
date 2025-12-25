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
        <head>
            <title>EthioStep Finance Bot</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }
                .container {
                    background: rgba(0, 0, 0, 0.7);
                    padding: 30px;
                    border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    max-width: 600px;
                    width: 90%;
                }
                h1 {
                    color: #4CAF50;
                    margin-bottom: 20px;
                }
                .status {
                    color: #4CAF50;
                    font-size: 24px;
                    font-weight: bold;
                    margin: 20px 0;
                }
                .info {
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ ETHIOSTEP FINANCE BOT</h1>
                <div class="status">LIVE 24/7 ON RENDER</div>
                
                <div class="info">
                    <p><strong>💰 Investment Platform</strong></p>
                    <p>10-Day Fixed Returns</p>
                    <p>Agent & VIP System</p>
                    <p>Daily Earnings</p>
                </div>
                
                <div class="info">
                    <p><strong>📱 Telegram Bot:</strong></p>
                    <p>@EthioStepFinanceBot</p>
                </div>
                
                <div class="info">
                    <p><strong>👤 Admin Support:</strong></p>
                    <p>@EthioStepAdmin</p>
                </div>
                
                <div style="margin-top: 30px; font-size: 14px; opacity: 0.8;">
                    <p>⏰ Server Time: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                    <p>🚀 Powered by Render.com</p>
                </div>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "service": "ethiostep-bot",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "features": ["investment", "agent_system", "vip_program", "referral_system"]
    }

@app.route('/ping')
def ping():
    return "pong"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Start Flask server in background
Thread(target=run_flask, daemon=True).start()
print("🌐 Flask server started on port 10000")

# ==================== TELEGRAM BOT ====================
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    print("❌ ERROR: BOT_TOKEN not set!")
    print("💡 Go to Render → Environment → Add BOT_TOKEN variable")
    exit(1)

bot = telebot.TeleBot(TOKEN)
print(f"✅ Bot token loaded: {TOKEN[:10]}...")

# ==================== DATABASE (IN-MEMORY) ====================
users_db = {}
investments_db = {}
payments_db = {}
agents_db = {}
vip_queue = []
referral_links = {}

# ==================== PAYMENT DETAILS (YOUR ACCOUNTS) ====================
PAYMENT_DETAILS = {
    'cbe_bank': {
        'account': '1000601221911',
        'name': 'ETHIOSTEP FINANCE',
        'bank': 'COMMERCIAL BANK OF ETHIOPIA',
        'branch': 'ADDIS ABABA MAIN'
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
    '1': {'id': '1', 'name': 'STARTER', 'amount': 20, 'return': 80, 'days': 10, 'profit': 60},
    '2': {'id': '2', 'name': 'PREMIUM', 'amount': 50, 'return': 100, 'days': 10, 'profit': 50},
    '3': {'id': '3', 'name': 'GOLD', 'amount': 100, 'return': 200, 'days': 10, 'profit': 100},
    'vip': {'id': 'vip', 'name': 'VIP', 'amount': 1000, 'return': 5000, 'days': 10, 'profit': 4000}
}

EXCHANGE_RATE = 57.5  # 1 USDT = 57.5 ETB

# ==================== HELPER FUNCTIONS ====================
def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            'id': user_id,
            'name': '',
            'username': '',
            'phone': '',
            'balance': 0.0,
            'total_invested': 0.0,
            'total_earned': 0.0,
            'referral_code': f"REF{user_id}{hashlib.md5(str(user_id).encode()).hexdigest()[:4]}",
            'referrals': [],
            'referral_earnings': 0.0,
            'is_agent': False,
            'agent_id': None,
            'is_manager': False,
            'manager_id': None,
            'vip_level': 0,
            'investments': [],
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
    return users_db[user_id]

def save_user(user_id, data):
    users_db[user_id] = data

def create_investment(user_id, plan_id):
    plan = INVESTMENT_PLANS[plan_id]
    investment_id = f"INV{user_id}{int(time.time())}"
    
    investment = {
        'id': investment_id,
        'user_id': user_id,
        'plan': plan,
        'amount_usd': plan['amount'],
        'amount_etb': plan['amount'] * EXCHANGE_RATE,
        'status': 'pending_payment',
        'start_date': datetime.now().isoformat(),
        'end_date': (datetime.now() + timedelta(days=plan['days'])).isoformat(),
        'expected_return': plan['return'],
        'profit': plan['profit']
    }
    
    investments_db[investment_id] = investment
    
    # Add to user's investments
    user = get_user(user_id)
    user['investments'].append(investment_id)
    
    return investment

def generate_referral_link(user_id):
    user = get_user(user_id)
    return f"https://t.me/EthioStepFinanceBot?start={user['referral_code']}"

def calculate_vip_daily():
    if vip_queue:
        last_vip = vip_queue[-1]
        daily_earnings = last_vip['amount'] * 0.7  # 70% daily
        return daily_earnings
    return 0

# ==================== BOT COMMANDS ====================
@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    user = message.from_user
    user_id = user.id
    
    # Get or create user
    user_data = get_user(user_id)
    user_data['name'] = user.first_name
    user_data['username'] = user.username
    user_data['last_active'] = datetime.now().isoformat()
    
    # Check for referral code in command
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        # Find referrer
        for uid, data in users_db.items():
            if data['referral_code'] == ref_code and uid != user_id:
                # Add referral bonus
                users_db[uid]['referrals'].append(user_id)
                users_db[uid]['referral_earnings'] += 10.0
                user_data['referred_by'] = uid
                break
    
    save_user(user_id, user_data)
    
    # Welcome message
    welcome = f"""
👋 *WELCOME {user.first_name}!*

🏦 *ETHIOSTEP FINANCE PLATFORM*
*Smart Investments • Fixed Returns • Daily Earnings*

💰 *YOUR WALLET*
• Balance: *${user_data['balance']:.2f}*
• Invested: *${user_data['total_invested']:.2f}*
• Earned: *${user_data['total_earned']:.2f}*

🎯 *QUICK ACTIONS:*
1️⃣ /invest - Investment Plans
2️⃣ /deposit - Add Funds  
3️⃣ /withdraw - Withdraw Money
4️⃣ /referral - Refer & Earn $10
5️⃣ /agent - Agent Program
6️⃣ /vip - VIP System
7️⃣ /wallet - My Wallet
8️⃣ /support - 24/7 Support

🔗 *Your Referral Code:*
`{user_data['referral_code']}`
👥 Referrals: *{len(user_data['referrals'])} users*
💸 Bonus: *${user_data['referral_earnings']:.2f}*

💎 *Start with $20 → Get $80 in 10 Days!*"""
    
    # Create keyboard
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        telebot.types.KeyboardButton("💰 INVEST"),
        telebot.types.KeyboardButton("💳 DEPOSIT"),
        telebot.types.KeyboardButton("👥 REFER"),
        telebot.types.KeyboardButton("🤝 AGENT"),
        telebot.types.KeyboardButton("👑 VIP"),
        telebot.types.KeyboardButton("📊 WALLET"),
        telebot.types.KeyboardButton("📞 SUPPORT")
    )
    
    bot.send_message(message.chat.id, welcome, 
                    parse_mode='Markdown',
                    reply_markup=keyboard)
    
    print(f"✅ User {user_id} started bot")

@bot.message_handler(commands=['deposit'])
def deposit_command(message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    deposit_text = f"""
💳 *DEPOSIT FUNDS TO INVEST*

*CHOOSE PAYMENT METHOD:*

🇪🇹 *FOR ETHIOPIAN USERS:*
🏦 *CBE BANK*
• Account: `{PAYMENT_DETAILS['cbe_bank']['account']}`
• Name: {PAYMENT_DETAILS['cbe_bank']['name']}
• Bank: {PAYMENT_DETAILS['cbe_bank']['bank']}

📱 *CBE BIRR*
• Number: `{PAYMENT_DETAILS['cbebirr']['number']}`
• Name: {PAYMENT_DETAILS['cbebirr']['name']}

📱 *TELEBIRR*
• Number: `{PAYMENT_DETAILS['telebirr']['number']}`
• Name: {PAYMENT_DETAILS['telebirr']['name']}

🇰🇪 *M-PESA (KENYA)*
• Number: `{PAYMENT_DETAILS['mpesa']['number']}`
• Name: {PAYMENT_DETAILS['mpesa']['name']}

🌍 *INTERNATIONAL (USDT)*
💎 *USDT TRC-20*
• Address: `{PAYMENT_DETAILS['usdt']['address']}`
• Network: {PAYMENT_DETAILS['usdt']['network']}

💱 *Exchange Rate:* 1 USDT = {EXCHANGE_RATE} ETB

⚠️ *IMPORTANT INSTRUCTIONS:*
1. Send *EXACT AMOUNT* for your chosen plan
2. Take *CLEAR SCREENSHOT* of payment
3. Send screenshot here immediately
4. Include your *NAME* in message
5. Wait for admin confirmation (15-30 minutes)

✅ *Your investment activates immediately after confirmation!*

📸 *AFTER PAYMENT, SEND SCREENSHOT HERE...*"""
    
    bot.send_message(message.chat.id, deposit_text, parse_mode='Markdown')
    
    # Inline keyboard for quick actions
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("📸 SEND SCREENSHOT", callback_data='send_screenshot'),
        telebot.types.InlineKeyboardButton("💰 VIEW PLANS", callback_data='view_plans'),
        telebot.types.InlineKeyboardButton("📞 CONTACT ADMIN", url='https://t.me/EthioStepAdmin')
    )
    
    bot.send_message(message.chat.id, "Quick actions:", reply_markup=keyboard)

@bot.message_handler(commands=['invest'])
def invest_command(message):
    invest_text = f"""
💰 *INVESTMENT PLANS*

🎯 *10-DAY FIXED RETURNS*

1️⃣ *STARTER PLAN*
• Invest: *${INVESTMENT_PLANS['1']['amount']}* ({INVESTMENT_PLANS['1']['amount'] * EXCHANGE_RATE:.0f} ETB)
• Returns: *${INVESTMENT_PLANS['1']['return']}* after {INVESTMENT_PLANS['1']['days']} days
• Profit: *${INVESTMENT_PLANS['1']['profit']}* (+300%)

2️⃣ *PREMIUM PLAN*
• Invest: *${INVESTMENT_PLANS['2']['amount']}* ({INVESTMENT_PLANS['2']['amount'] * EXCHANGE_RATE:.0f} ETB)
• Returns: *${INVESTMENT_PLANS['2']['return']}* after {INVESTMENT_PLANS['2']['days']} days
• Profit: *${INVESTMENT_PLANS['2']['profit']}* (+100%)

3️⃣ *GOLD PLAN*
• Invest: *${INVESTMENT_PLANS['3']['amount']}* ({INVESTMENT_PLANS['3']['amount'] * EXCHANGE_RATE:.0f} ETB)
• Returns: *${INVESTMENT_PLANS['3']['return']}* after {INVESTMENT_PLANS['3']['days']} days
• Profit: *${INVESTMENT_PLANS['3']['profit']}* (+100%)

👑 *VIP PLAN* 👑
• Invest: *${INVESTMENT_PLANS['vip']['amount']}* ({INVESTMENT_PLANS['vip']['amount'] * EXCHANGE_RATE:.0f} ETB)
• Returns: *${INVESTMENT_PLANS['vip']['return']}* after {INVESTMENT_PLANS['vip']['days']} days
• Profit: *${INVESTMENT_PLANS['vip']['profit']}* (+400%)
• *SPECIAL:* Manager gets 70% daily from VIP investment

📝 *HOW TO INVEST:*
1. Choose plan (reply with number 1, 2, 3, or VIP)
2. Use /deposit for payment instructions
3. Send payment screenshot
4. Get confirmation from admin
5. Start earning!

💡 *Tip:* VIP members get priority processing!"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("💰 PLAN 1 ($20)", callback_data='plan_1'),
        telebot.types.InlineKeyboardButton("💰 PLAN 2 ($50)", callback_data='plan_2'),
        telebot.types.InlineKeyboardButton("💰 PLAN 3 ($100)", callback_data='plan_3'),
        telebot.types.InlineKeyboardButton("👑 VIP ($1000)", callback_data='plan_vip'),
        telebot.types.InlineKeyboardButton("💳 DEPOSIT NOW", callback_data='deposit_now')
    )
    
    bot.send_message(message.chat.id, invest_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['referral'])
def referral_command(message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    ref_link = generate_referral_link(user_id)
    
    referral_text = f"""
👥 *REFERRAL PROGRAM*

💰 *EARN $10 FOR EVERY FRIEND!*

🔗 *Your Referral Link:*
`{ref_link}`

📋 *Your Referral Code:*
`{user_data['referral_code']}`

📊 *YOUR STATISTICS:*
• Total Referrals: *{len(user_data['referrals'])}*
• Referral Earnings: *${user_data['referral_earnings']:.2f}*
• Available to Withdraw: *${user_data['referral_earnings']:.2f}*

🎯 *HOW IT WORKS:*
1. Share your link with friends
2. Friend clicks link & registers
3. Friend makes first investment
4. You get $10 instantly!

💰 *REFERRAL BONUS STRUCTURE:*
• Level 1: $10 per direct referral
• Level 2: $5 (when your referral refers someone)
• Level 3: $2 (second level referrals)

🤝 *BECOME AGENT:* /agent
*(Earn 20% commission from your team)*

💎 *UPGRADE TO VIP:* /vip
*(Get 70% daily earnings as Manager)*"""

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("📤 SHARE LINK", switch_inline_query=f"Join EthioStep! Earn with me! {ref_link}"),
        telebot.types.InlineKeyboardButton("🤝 BECOME AGENT", callback_data='become_agent'),
        telebot.types.InlineKeyboardButton("👑 BECOME VIP", callback_data='become_vip'),
        telebot.types.InlineKeyboardButton("📊 MY TEAM", callback_data='my_team')
    )
    
    bot.send_message(message.chat.id, referral_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['agent'])
def agent_command(message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    if not user_data['is_agent']:
        # Show agent enrollment info
        agent_text = """
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

💰 *MANAGER PROGRAM:*
When you enroll the LAST VIP, you become MANAGER
• Get 70% daily from last VIP's investment
• Manage team of agents
• Higher commission rates
• Priority support

💵 *UPGRADE TO AGENT:*
Send $50 registration fee to become agent
Contact admin: @EthioStepAdmin

📈 *CURRENT VIP DAILY EARNINGS:*
Last VIP generates ${calculate_vip_daily():.2f} daily for their Manager!"""
    else:
        # Show agent dashboard
        agent_text = f"""
👨‍💼 *AGENT DASHBOARD*

🆔 Agent ID: `AGT{user_id}`
⭐ Level: {'MANAGER' if user_data['is_manager'] else 'AGENT'}

💰 *EARNINGS SUMMARY:*
• Today: $0.00
• This Week: $0.00
• Total: ${user_data.get('agent_earnings', 0):.2f}

👥 *TEAM STATISTICS:*
• Direct Team: {len([r for r in user_data['referrals']])} agents
• Total Team: 0 people
• Team Investment: $0.00

📈 *MANAGER BONUS (If Manager):*
Last VIP Daily 70%: ${calculate_vip_daily():.2f}

🔗 *Your Agent Link:*
`https://t.me/EthioStepFinanceBot?start=agent_{user_id}`"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("📊 MY TEAM", callback_data='agent_team'),
        telebot.types.InlineKeyboardButton("💰 WITHDRAW", callback_data='agent_withdraw'),
        telebot.types.InlineKeyboardButton("👑 ENROLL VIP", callback_data='enroll_vip'),
        telebot.types.InlineKeyboardButton("📞 ADMIN", url='https://t.me/EthioStepAdmin')
    )
    
    bot.send_message(message.chat.id, agent_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['vip'])
def vip_command(message):
    vip_text = f"""
👑 *VIP PROGRAM*

💰 *INVEST $1000 → GET $5000 IN 10 DAYS!*

🎯 *VIP BENEFITS:*
• 500% return in 10 days
• Priority support 24/7
• Daily earnings for your Manager
• Special VIP status badge
• Faster withdrawals

⚡ *VIP DAILY EARNINGS SYSTEM:*
Last enrolled VIP generates 70% daily earnings for their Manager!

📊 *CURRENT VIP QUEUE:*
"""
    
    # Show VIP queue
    if vip_queue:
        vip_text += f"Total VIPs: {len(vip_queue)}\n\n"
        for i, vip in enumerate(vip_queue[-5:], 1):  # Show last 5 VIPs
            vip_text += f"{i}. VIP Member - ${vip['amount']:.0f}\n"
        
        last_vip = vip_queue[-1]
        vip_text += f"\n💰 *LAST VIP DAILY EARNINGS:*\n"
        vip_text += f"Manager earns *${last_vip['amount'] * 0.7:.2f}* daily!\n"
    else:
        vip_text += "No VIPs yet. Be the first VIP!\n"
    
    vip_text += f"""
💎 *HOW TO BECOME VIP:*
1. Invest $1000 (VIP Plan)
2. Contact Admin @EthioStepAdmin
3. Get VIP status confirmation
4. Start earning for your Manager
5. Receive $5000 after 10 days

🤝 *HOW TO ENROLL VIP (For Agents):*
1. Refer someone to invest $1000
2. They mention your Agent ID
3. Admin will connect you as Manager
4. You earn 70% daily from their investment

📞 *Contact Admin to become VIP:* @EthioStepAdmin"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("👑 BECOME VIP", callback_data='become_vip'),
        telebot.types.InlineKeyboardButton("🤝 ENROLL VIP", callback_data='enroll_vip'),
        telebot.types.InlineKeyboardButton("📊 VIP QUEUE", callback_data='vip_queue'),
        telebot.types.InlineKeyboardButton("💰 CALCULATE", callback_data='calculate_earnings')
    )
    
    bot.send_message(message.chat.id, vip_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['wallet'])
def wallet_command(message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    wallet_text = f"""
💼 *YOUR WALLET*

👤 Account: {user_data['name']}
🆔 User ID: {user_id}
📅 Member Since: {user_data['created_at'][:10]}

💰 *BALANCES:*
• Available Balance: *${user_data['balance']:.2f}*
• Invested Amount: *${user_data['total_invested']:.2f}*
• Total Earned: *${user_data['total_earned']:.2f}*
• Referral Earnings: *${user_data['referral_earnings']:.2f}*

📊 *STATISTICS:*
• Active Investments: {len(user_data['investments'])}
• Total Referrals: {len(user_data['referrals'])}
• VIP Level: {user_data['vip_level']}
• Agent Status: {'✅ ACTIVE' if user_data['is_agent'] else '❌ INACTIVE'}

💳 *WITHDRAWAL OPTIONS:*
• Minimum Withdrawal: $20
• Processing Time: 24-48 hours
• Available Methods: USDT, Telebirr, CBE, M-Pesa

📝 *To withdraw, use:* /withdraw"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("💰 WITHDRAW", callback_data='withdraw_funds'),
        telebot.types.InlineKeyboardButton("💳 DEPOSIT MORE", callback_data='deposit_now'),
        telebot.types.InlineKeyboardButton("📊 INVESTMENTS", callback_data='my_investments'),
        telebot.types.InlineKeyboardButton("📞 SUPPORT", url='https://t.me/EthioStepSupport')
    )
    
    bot.send_message(message.chat.id, wallet_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['withdraw'])
def withdraw_command(message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    withdraw_text = f"""
💰 *WITHDRAW EARNINGS*

💼 *Available Balance:* ${user_data['balance']:.2f}

⚠️ *WITHDRAWAL RULES:*
• Minimum Amount: $20
• Processing Time: 24-48 hours
• Commission: 5% (network fees)
• Daily Limit: $500 per day

💳 *AVAILABLE METHODS:*
1. USDT (TRC-20)
2. Telebirr
3. CBE Bank
4. M-Pesa

📝 *HOW TO WITHDRAW:*
1. Ensure minimum balance ($20+)
2. Choose withdrawal method
3. Enter amount
4. Provide details (wallet/bank info)
5. Submit request
6. Wait for processing

⏰ *Processing Schedule:*
• Requests processed daily at 10:00 AM & 4:00 PM
• Weekends may have delays
• Contact support for urgent requests

📞 *Support:* @EthioStepSupport"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("💎 USDT WITHDRAW", callback_data='withdraw_usdt'),
        telebot.types.InlineKeyboardButton("📱 TELEBIRR", callback_data='withdraw_telebirr'),
        telebot.types.InlineKeyboardButton("🏦 CBE BANK", callback_data='withdraw_cbe'),
        telebot.types.InlineKeyboardButton("📲 M-PESA", callback_data='withdraw_mpesa'),
        telebot.types.InlineKeyboardButton("📞 SUPPORT", url='https://t.me/EthioStepSupport')
    )
    
    bot.send_message(message.chat.id, withdraw_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['support'])
def support_command(message):
    support_text = """
📞 *24/7 SUPPORT & CONTACT*

👤 *ADMIN:* @EthioStepAdmin
📢 *ANNOUNCEMENTS:* @EthioStepNews
👥 *COMMUNITY:* @EthioStepCommunity

⏰ *SUPPORT HOURS:* 24/7
⚡ *RESPONSE TIME:* < 30 minutes

🔧 *WE CAN HELP WITH:*
• Payment Issues
• Investment Activation
• Withdrawal Processing
• Account Problems
• Technical Support
• Agent/VIP Enrollment

📋 *WHEN CONTACTING ADMIN:*
1. Your Name & User ID
2. Transaction Details
3. Screenshots (if any)
4. Clear description of issue
5. Be patient for response

⚠️ *EMERGENCY CONTACT:*
For urgent issues, mention "URGENT" in message

✅ *BOT STATUS:* ONLINE 🟢 24/7
🏠 *HOSTED ON:* Render.com
🔒 *SECURE:* SSL Encrypted"""
    
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("👤 CONTACT ADMIN", url='https://t.me/EthioStepAdmin'),
        telebot.types.InlineKeyboardButton("📢 NEWS CHANNEL", url='https://t.me/EthioStepNews'),
        telebot.types.InlineKeyboardButton("👥 COMMUNITY", url='https://t.me/EthioStepCommunity'),
        telebot.types.InlineKeyboardButton("🌐 WEBSITE", url='https://ethiostep-bot.onrender.com')
    )
    
    bot.send_message(message.chat.id, support_text, parse_mode='Markdown', reply_markup=keyboard)

# ==================== HANDLE SCREENSHOTS ====================
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Confirm receipt
    confirmation = f"""
✅ *SCREENSHOT RECEIVED!*

Thank you {user_name}! 

📋 *Payment Details Registered:*
• User: {user_name}
• User ID: {user_id}
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Status: *UNDER REVIEW*

⏳ *Processing Information:*
• Review Time: 15-30 minutes
• Admin will verify payment
• You'll receive confirmation
• Investment activates immediately after approval

💬 *Stay online for confirmation message.*
📞 *Contact @EthioStepAdmin if urgent.*"""
    
    bot.reply_to(message, confirmation, parse_mode='Markdown')
    
    # Notify admin (REPLACE 123456789 with YOUR Telegram ID)
    admin_id = 123456789  # ⚠️ CHANGE THIS TO YOUR ADMIN ID!
    try:
        # Forward screenshot to admin
        bot.forward_message(admin_id, message.chat.id, message.message_id)
        
        # Send notification to admin
        admin_msg = f"""
📸 *NEW PAYMENT SCREENSHOT*
        
👤 From: {user_name} (@{message.from_user.username})
🆔 User ID: {user_id}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        
💬 *Message:* "{message.caption if message.caption else 'No caption'}"
        
✅ *Actions:*
1. Verify payment
2. Activate investment
3. Notify user"""
        
        bot.send_message(admin_id, admin_msg, parse_mode='Markdown')
        
        print(f"📸 Screenshot forwarded to admin from user {user_id}")
    except Exception as e:
        print(f"⚠️ Could not notify admin: {e}")

# ==================== HANDLE TEXT MESSAGES ====================
@bot.message_handler(func=lambda message: message.text in ['💰 INVEST', '💳 DEPOSIT', '👥 REFER', '🤝 AGENT', '👑 VIP', '📊 WALLET', '📞 SUPPORT'])
def handle_button_click(message):
    if message.text == '💰 INVEST':
        invest_command(message)
    elif message.text == '💳 DEPOSIT':
        deposit_command(message)
    elif message.text == '👥 REFER':
        referral_command(message)
    elif message.text == '🤝 AGENT':
        agent_command(message)
    elif message.text == '👑 VIP':
        vip_command(message)
    elif message.text == '📊 WALLET':
        wallet_command(message)
    elif message.text == '📞 SUPPORT':
        support_command(message)

@bot.message_handler(func=lambda message: message.text in ['1', '2', '3', 'vip', 'VIP'])
def handle_plan_selection(message):
    plan_id = message.text.lower()
    
    if plan_id in INVESTMENT_PLANS:
        plan = INVESTMENT_PLANS[plan_id]
        etb_amount = plan['amount'] * EXCHANGE_RATE
        
        response = f"""
✅ *{plan['name']} PLAN SELECTED*

📋 *INVESTMENT DETAILS:*
• Amount: *${plan['amount']}*
• In ETB: *{etb_amount:.0f} Birr*
• Returns: *${plan['return']}* after {plan['days']} days
• Profit: *${plan['profit']}* (+{(plan['profit']/plan['amount'])*100:.0f}%)

💳 *NEXT STEPS:*
1. Use /deposit for payment instructions
2. Make payment to provided account
3. Send payment screenshot here
4. Wait for admin confirmation
5. Investment activates immediately!

📞 *Need help?* Contact @EthioStepAdmin
        
💡 *Tip:* VIP members get 70% daily earnings for their Manager!"""
        
        # Store selected plan for user
        user_id = message.from_user.id
        user_data = get_user(user_id)
        user_data['selected_plan'] = plan_id
        save_user(user_id, user_data)
        
        bot.reply_to(message, response, parse_mode='Markdown')

# ==================== CALLBACK QUERY HANDLER ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if call.data == 'send_screenshot':
        bot.answer_callback_query(call.id, "📸 Please send your payment screenshot now!")
        bot.send_message(call.message.chat.id, "Please take a CLEAR screenshot of your payment and send it here.")
    
    elif call.data == 'view_plans':
        invest_command(call.message)
    
    elif call.data == 'deposit_now':
        deposit_command(call.message)
    
    elif call.data.startswith('plan_'):
        plan_map = {
            'plan_1': '1',
            'plan_2': '2',
            'plan_3': '3',
            'plan_vip': 'vip'
        }
        
        if call.data in plan_map:
            plan_id = plan_map[call.data]
            plan = INVESTMENT_PLANS[plan_id]
            
            response = f"""
✅ *{plan['name']} PLAN SELECTED*

💰 Investment: ${plan['amount']}
🎯 Returns: ${plan['return']} in {plan['days']} days
📈 Profit: ${plan['profit']}
        
💳 *Click below to proceed with payment:*"""
            
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(
                telebot.types.InlineKeyboardButton("💳 PAY NOW", callback_data='deposit_now'),
                telebot.types.InlineKeyboardButton("📞 ASK ADMIN", url='https://t.me/EthioStepAdmin')
            )
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    elif call.data == 'become_vip':
        vip_info = """
👑 *TO BECOME VIP:*

1. Invest $1000 (VIP Plan)
2. Contact @EthioStepAdmin with payment proof
3. You'll be added to VIP queue
4. Your Manager earns 70% daily from your investment

💎 *VIP Benefits:*
• $5000 return in 10 days
• Priority 24/7 support
• Special VIP status
• Faster withdrawals

📞 *Contact Admin Now:* @EthioStepAdmin"""
        
        bot.send_message(call.message.chat.id, vip_info, parse_mode='Markdown')
    
    elif call.data == 'enroll_vip':
        enroll_info = """
🤝 *ENROLL VIP MEMBER*

As an Agent/Manager, you can enroll VIP members:

📋 *Requirements to Enroll VIP:*
1. You must be active Agent
2. VIP invests $1000
3. You become their Manager
4. You get 70% daily from their investment

💰 *Your Daily Earnings:*
For each VIP you enroll: $700 daily for 10 days!

📝 *How to Enroll:*
1. Refer someone to invest $1000
2. They mention your Agent ID during registration
3. Contact admin @EthioStepAdmin
4. You'll be connected as Manager
5. Start earning daily 70%

📞 *Contact Admin for enrollment:* @EthioStepAdmin"""
        
        bot.send_message(call.message.chat.id, enroll_info, parse_mode='Markdown')
    
    bot.answer_callback_query(call.id)

# ==================== ADMIN COMMANDS ====================
@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    
    # ⚠️ CHANGE THIS TO YOUR TELEGRAM ID!
    if user_id != 123456789:  # REPLACE WITH YOUR ADMIN ID
        bot.reply_to(message, "❌ Admin access required.")
        return
    
    admin_text = f"""
🔧 *ADMIN PANEL*

📊 *SYSTEM STATISTICS:*
• Total Users: {len(users_db)}
• Active Investments: {len(investments_db)}
• VIP Members: {len(vip_queue)}
• Total Agents: {len([u for u in users_db.values() if u['is_agent']])}

💰 *FINANCIAL OVERVIEW:*
• Total Invested: ${sum(u['total_invested'] for u in users_db.values()):.2f}
• Total Paid Out: ${sum(u['total_earned'] for u in users_db.values()):.2f}
• Platform Balance: $0.00

👑 *VIP QUEUE:*
• Last VIP Daily: ${calculate_vip_daily():.2f}
• Queue Length: {len(vip_queue)}

🛠 *ADMIN COMMANDS:*
• /users - View all users
• /investments - View investments
• /payments - Pending payments
• /approve - Approve payment
• /add_vip - Add VIP member
• /stats - Detailed statistics"""

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("👥 USERS", callback_data='admin_users'),
        telebot.types.InlineKeyboardButton("💰 INVESTMENTS", callback_data='admin_investments'),
        telebot.types.InlineKeyboardButton("✅ APPROVE", callback_data='admin_approve'),
        telebot.types.InlineKeyboardButton("📊 STATS", callback_data='admin_stats')
    )
    
    bot.send_message(message.chat.id, admin_text, parse_mode='Markdown', reply_markup=keyboard)

# ==================== START BOT ====================
print("=" * 60)
print("🚀 ETHIOSTEP FINANCE BOT - VERSION 2.0")
print("🏠 Host: Render.com | 24/7 Operation")
print("💰 Features: Investment, Agent System, VIP Program")
print("👥 Referral System | Manager 70% Daily Earnings")
print("=" * 60)
print("📅 Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("🤖 Bot is starting...")

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    
    while True:
        try:
            print(f"📡 [{datetime.now().strftime('%H:%M:%S')}] Polling for messages...")
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"⚠️ Error: {str(e)}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10)
