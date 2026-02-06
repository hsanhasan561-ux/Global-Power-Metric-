import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

# ১. ডাটাবেস ইঞ্জিন সেটআপ
conn = sqlite3.connect('global_power_metric.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, full_name TEXT, 
                 ref_by TEXT, side TEXT, balance REAL, status TEXT, 
                 bkash TEXT, rank TEXT, kyc_status TEXT, trx_id TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, type TEXT, amount REAL, date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS withdraw_requests 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, amount REAL, method TEXT, status TEXT, date TEXT)''')
    
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users VALUES ('admin', ?, 'Chief Admin', 'None', 'None', 0.0, 'Active', '01700', 'CEO', 'Verified', 'MASTER')")
    conn.commit()

init_db()

# ২. সিকিউরিটি ফাংশন
def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ৩. প্রফেশনাল UI ডিজাইন
st.set_page_config(page_title="Global Power Metric", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .main-title { color: #00d4ff; text-align: center; font-size: 40px; font-weight: bold; text-shadow: 0 0 10px #00d4ff; }
    .metric-card { background: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #30363d; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ GLOBAL POWER METRIC ⚡</div>', unsafe_allow_html=True)

# ৪. অথেন্টিকেশন সিস্টেম
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 লগইন", "📝 রেজিস্ট্রেশন"])
    
    with tab1:
        u = st.text_input("ইউজারনেম")
        p = st.text_input("পাসওয়ার্ড", type="password")
        if st.button("লগইন করুন"):
            user_hash = hash_pass(p)
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, user_hash))
            data = c.fetchone()
            if data:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("ভুল ইউজারনেম বা পাসওয়ার্ড!")

    with tab2:
        new_u = st.text_input("ইউজারনেম দিন")
        new_p = st.text_input("পাসওয়ার্ড দিন", type="password")
        ref_id = st.text_input("স্পন্সর আইডি")
        side = st.selectbox("পজিশন", ["Left", "Right"])
        st.info("অ্যাক্টিভেশন ফি: ৫০০ টাকা। বিকাশ: ০১৭XXXXXXXX")
        trx = st.text_input("Transaction ID (TrxID)")
        
        if st.button("রেজিস্ট্রেশন করুন"):
            if new_u and new_p and ref_id and trx:
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                              (new_u, hash_pass(new_p), new_u, ref_id, side, 0.0, 'Pending', '', 'Member', 'Pending', trx))
                    conn.commit()
                    st.success("আবেদন সফল! অ্যাডমিন যাচাই করে একটিভ করে দিবে।")
                except:
                    st.error("এই ইউজারনেমটি আগেই ব্যবহার হয়েছে।")

else:
    # ৫. ড্যাশবোর্ড
    user = st.session_state.user
    c.execute("SELECT * FROM users WHERE username=?", (user,))
    user_info = c.fetchone()

    st.sidebar.title("⚡ GPM প্যানেল")
    menu = st.sidebar.radio("মেনু", ["ড্যাশবোর্ড", "আমার টিম", "উইথড্র", "অ্যাডমিন প্যানেল"])

    if menu == "ড্যাশবোর্ড":
        st.subheader(f"স্বাগতম, {user_info[2]}")
        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="metric-card"><h3>ব্যালেন্স</h3><h2>৳{user_info[5]}</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><h3>স্ট্যাটাস</h3><h2>{user_info[6]}</h2></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><h3>র‍্যাঙ্ক</h3><h2>{user_info[8]}</h2></div>', unsafe_allow_html=True)
        
        st.write("---")
        if st.button("💰 ডেইলি ROI সংগ্রহ করুন"):
            st.success("৳২০ আপনার ওয়ালেটে যোগ হয়েছে!")

    elif menu == "অ্যাডমিন প্যানেল":
        if user != "admin":
            st.error("শুধুমাত্র অ্যাডমিনের জন্য!")
        else:
            st.subheader("পেন্ডিং রিকোয়েস্ট")
            df = pd.read_sql("SELECT username, trx_id, status FROM users WHERE status='Pending'", conn)
            st.table(df)
            app_u = st.text_input("একটিভ করতে ইউজারনেম লিখুন")
            if st.button("কনফার্ম করুন"):
                c.execute("UPDATE users SET status='Active' WHERE username=?", (app_u,))
                conn.commit()
                st.success(f"{app_u} একটিভ হয়েছে!")

    if st.sidebar.button("লগআউট"):
        st.session_state.logged_in = False
        st.rerun()
  
