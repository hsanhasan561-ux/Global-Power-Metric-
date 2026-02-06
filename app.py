import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

# -----------------------------
# ১. ডাটাবেস কানেকশন
# -----------------------------
conn = sqlite3.connect('global_power_metric.db', check_same_thread=False)
c = conn.cursor()

# -----------------------------
# ২. ডাটাবেস ইন্টি-ফাংশন
# -----------------------------
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, full_name TEXT, 
                 ref_by TEXT, side TEXT, balance REAL, status TEXT, 
                 bkash TEXT, rank TEXT, kyc_status TEXT, trx_id TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, type TEXT, amount REAL, date TEXT)''')

    # অ্যাডমিন একাউন্ট চেক
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users VALUES ('admin', ?, 'Chief Admin', 'None', 'None', 0.0, 'Active', '01700', 'CEO', 'Verified', 'MASTER')", (admin_pass,))
    conn.commit()

init_db()

# -----------------------------
# ৩. পাসওয়ার্ড হ্যাশ ফাংশন
# -----------------------------
def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# -----------------------------
# ৪. ব্যালেন্স আপডেট / ট্রানজ্যাকশন ফাংশন
# -----------------------------
def add_transaction(user, type_, amount):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO transactions (user, type, amount, date) VALUES (?,?,?,?)",
              (user, type_, amount, now))
    c.execute("SELECT balance FROM users WHERE username=?", (user,))
    current_balance = c.fetchone()[0]
    if type_ == "Deposit":
        new_balance = current_balance + amount
    else:
        new_balance = current_balance - amount
    c.execute("UPDATE users SET balance=? WHERE username=?", (new_balance, user))
    conn.commit()
    return new_balance

# -----------------------------
# ৫. Streamlit UI সেটআপ
# -----------------------------
st.set_page_config(page_title="Global Power Metric", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .main-title { color: #00d4ff; text-align: center; font-size: 40px; font-weight: bold; text-shadow: 0 0 10px #00d4ff; }
    .tab-card { background: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ GLOBAL POWER METRIC ⚡</div>', unsafe_allow_html=True)

# -----------------------------
# ৬. অথেন্টিকেশন স্টেট
# -----------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# -----------------------------
# ৭. লগইন / রেজিস্ট্রেশন পেজ
# -----------------------------
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 লগইন", "📝 রেজিস্ট্রেশন"])
    
    with tab1:
        with st.container():
            st.markdown('<div class="tab-card">', unsafe_allow_html=True)
            u = st.text_input("ইউজারনেম")
            p = st.text_input("পাসওয়ার্ড", type="password")
            if st.button("লগইন করুন"):
                user_hash = hash_pass(p)
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, user_hash))
                data = c.fetchone()
                if data:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.success(f"স্বাগতম, {data[2]}!")
                    st.experimental_rerun()
                else:
                    st.error("ভুল ইউজারনেম বা পাসওয়ার্ড!")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        with st.container():
            st.markdown('<div class="tab-card">', unsafe_allow_html=True)
            new_u = st.text_input("ইউজারনেম দিন", key="reg_user")
            new_p = st.text_input("পাসওয়ার্ড দিন", type="password", key="reg_pass")
            ref_id = st.text_input("স্পন্সর আইডি", key="reg_ref")
            side = st.selectbox("পজিশন", ["Left", "Right"], key="reg_side")
            st.info("অ্যাক্টিভেশন ফি: ৫০০ টাকা। বিকাশ: ০১৭XXXXXXXX")
            trx = st.text_input("Transaction ID (TrxID)", key="reg_trx")
            
            if st.button("রেজিস্ট্রেশন করুন"):
                if new_u and new_p and ref_id and trx:
                    try:
                        hp = hash_pass(new_p)
                        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                                  (new_u, hp, new_u, ref_id, side, 0.0, 'Pending', '', 'Member', 'Pending', trx))
                        conn.commit()
                        st.success("আবেদন সফল! অ্যাডমিন যাচাই করে একটিভ করে দিবে।")
                    except Exception as e:
                        st.error(f"এরর: {e}")
                else:
                    st.warning("সব ফিল্ড পূরণ করুন।")
            st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# ৮. হোম / ড্যাশবোর্ড পেজ
# -----------------------------
else:
    user = st.session_state.user
    c.execute("SELECT full_name, balance, status, rank FROM users WHERE username=?", (user,))
    data = c.fetchone()
    full_name, balance, status, rank = data

    st.markdown("---")
    st.markdown(f'<h2 style="color:#00d4ff;text-align:center;">🏠 হোম পেজ - স্বাগতম, {full_name}</h2>', unsafe_allow_html=True)

    # ব্যালেন্স / স্ট্যাটাস / র‍্যাঙ্ক কার্ডস
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"""
    <div style="background:#0d1117;padding:15px;border-radius:15px;border:1px solid #30363d;text-align:center;">
    <h4 style="color:#00d4ff;">ব্যালেন্স</h4>
    <h2 style="color:white;">৳{balance}</h2>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div style="background:#0d1117;padding:15px;border-radius:15px;border:1px solid #30363d;text-align:center;">
    <h4 style="color:#00d4ff;">স্ট্যাটাস</h4>
    <h2 style="color:white;">{status}</h2>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div style="background:#0d1117;padding:15px;border-radius:15px;border:1px solid #30363d;text-align:center;">
    <h4 style="color:#00d4ff;">র‍্যাঙ্ক</h4>
    <h2 style="color:white;">{rank}</h2>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------
    # ডিপোজিট / উইথড্র সেকশন
    # -----------------------------
    st.markdown("<h3 style='color:#00d4ff;'>💰 ব্যালেন্স আপডেট</h3>", unsafe_allow_html=True)
    trx_type = st.selectbox("টাইপ", ["Deposit", "Withdraw"])
    amount = st.number_input("পরিমাণ", min_value=0.0, step=100.0)
    if st.button("আপডেট করুন"):
        if amount <= 0:
            st.warning("পরিমাণ অবশ্যই 0 এর বেশি হতে হবে।")
        else:
            new_balance = add_transaction(user, trx_type, amount)
            st.success(f"সফল! নতুন ব্যালেন্স: ৳{new_balance}")

    # -----------------------------
    # প্ল্যান লিস্ট
    # -----------------------------
    st.markdown("<h3 style='color:#00d4ff;'>📦 প্ল্যানসমূহ</h3>", unsafe_allow_html=True)

    plans = [
        {"name": "Starter Plan", "amount": 500, "roi": "5% per month", "duration": "1 Month"},
        {"name": "Silver Plan", "amount": 2000, "roi": "7% per month", "duration": "3 Months"},
        {"name": "Gold Plan", "amount": 5000, "roi": "10% per month", "duration": "6 Months"},
        {"name": "Platinum Plan", "amount": 10000, "roi": "15% per month", "duration": "12 Months"},
    ]

    for plan in plans:
        st.markdown(f"""
        <div style="background:#161b22;padding:15px;margin-bottom:10px;border-radius:15px;border:1px solid #30363d;">
        <h4 style="color:#00d4ff;">{plan['name']}</h4>
        <p style="color:white;">💵 Amount: ৳{plan['amount']}</p>
        <p style="color:white;">📈 ROI: {plan['roi']}</p>
        <p style="color:white;">⏳ Duration: {plan['duration']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<br><p style="text-align:center;color:#888;">© 2026 Global Power Metric</p>', unsafe_allow_html=True)

    # -----------------------------
    # লগআউট
    # -----------------------------
    if st.sidebar.button("লগআউট"):
        st.session_state.logged_in = False
        st.experimental_rerun()
