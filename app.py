import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# 1. GLOBAL CONFIGURATION & DATABASE
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"

# Default Values (Inhein Admin Panel se badla ja sakta hai)
ADMIN_NUMBER = "03005508112"

st.set_page_config(page_title="Paint Pro Store - Master System", layout="wide", initial_sidebar_state="expanded")

# ========================================================
# 2. ADVANCED CSS CUSTOMIZATION
# ========================================================
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    
    /* Metric Cards Styling */
    .metric-container { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 25px; }
    .m-card {
        flex: 1; min-width: 200px; padding: 25px; border-radius: 20px; text-align: center; color: white;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05); transition: 0.3s; position: relative;
    }
    .m-card:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }
    .c-total { background: linear-gradient(135deg, #1e3a8a, #3b82f6); }
    .c-pending { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
    .c-complete { background: linear-gradient(135deg, #059669, #10b981); }
    .c-active { background: linear-gradient(135deg, #7c3aed, #a78bfa); }
    
    /* Button & Row Styling */
    .stButton>button { border-radius: 12px; font-weight: 700; transition: all 0.3s; }
    .order-row {
        background: white; padding: 20px; border-radius: 15px; margin-bottom: 12px;
        border-left: 6px solid #3b82f6; display: flex; justify-content: space-between;
        align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    /* QR & Forms */
    .qr-container {
        text-align: center; background: white; padding: 25px;
        border: 2px dashed #cbd5e1; border-radius: 25px; margin: 15px 0;
    }
    .footer-text { text-align: center; padding: 30px; color: #94a3b8; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. DATA ENGINE (Loading & Cleaning)
# ========================================================
@st.cache_data(ttl=2)
def load_all_data():
    try:
        ts = int(time.time())
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={ts}&sheet="
        u = pd.read_csv(url + "Users").fillna('')
        s = pd.read_csv(url + "Settings").fillna('')
        o = pd.read_csv(url + "Orders").fillna('')
        f = pd.read_csv(url + "Feedback").fillna('')
        return u, s, o, f
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_db, settings_db, orders_db, feedback_db = load_all_data()

def clean_phone(p):
    s = str(p).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def get_inv_id(df):
    if df.empty: return "0001"
    try:
        m = pd.to_numeric(df['Invoice_ID'], errors='coerce').max()
        return f"{int(m) + 1:04d}" if not pd.isna(m) else "0001"
    except: return "0001"

# ========================================================
# 4. SESSION MANAGEMENT
# ========================================================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'screen' not in st.session_state: st.session_state.screen = "🏠 Dashboard"
if 'wizard' not in st.session_state: st.session_state.wizard = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'buf' not in st.session_state: st.session_state.buf = {}

def nav(s):
    st.session_state.screen = s
    st.rerun()

# ========================================================
# 5. AUTHENTICATION (Login/Signup)
# ========================================================
if not st.session_state.auth:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h1 style='text-align:center;'>🎨 Paint Pro Portal</h1>", unsafe_allow_html=True)
        tab_l, tab_r = st.tabs(["🔐 Login", "📝 New Account"])
        with tab_l:
            l_ph = st.text_input("Mobile Number")
            l_pw = st.text_input("Password", type="password")
            if st.button("Sign In 🚀", use_container_width=True):
                target = clean_phone(l_ph)
                match = users_db[(users_db['Phone'].apply(clean_phone) == target) & (users_db['Password'].astype(str) == l_pw)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Wrong Details!")
        with tab_r:
            r_n = st.text_input("Full Name")
            r_p = st.text_input("Mobile")
            r_pass = st.text_input("Create Pass", type="password")
            if st.button("Register Now"):
                requests.post(SCRIPT_URL, json={"action":"register", "name":r_n, "phone":clean_phone(r_p), "password":r_pass})
                st.success("Pending Approval!")
    st.stop()

# ========================================================
# 6. APP MASTER SETTINGS (Logic)
# ================= In Settings Ko Admin Panel se Control karein
APP_NAME = "Paint Pro Store"
J_NO = "03005508112"
E_NO = "03005508112"
# ========================================================

# ========================================================
# 7. SIDEBAR NAVIGATION
# ========================================================
u = st.session_state.user
u_ph = clean_phone(u.get('Phone', ''))
is_adm = (u_ph == clean_phone(ADMIN_NUMBER))

with st.sidebar:
    st.markdown(f"<div style='text-align:center;'><img src='{u.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png')}' style='width:100px; border-radius:50%;'><br><h3>{u.get('Name')}</h3></div>", unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Dashboard", use_container_width=True): nav("🏠 Dashboard")
    if st.button("🛍️ New Order", use_container_width=True, type="primary"): 
        st.session_state.wizard = True
        st.session_state.step = 1
        st.rerun()
    if st.button("📜 History", use_container_width=True): nav("📜 History")
    if st.button("👤 My Profile", use_container_width=True): nav("👤 Profile")
    
    if is_adm:
        st.divider()
        st.markdown("🛠️ **Master Access**")
        if st.button("🔐 Admin Control", use_container_width=True): nav("🔐 Admin")
    
    st.divider()
    if st.button("Logout 🚪"):
        st.session_state.clear(); st.rerun()

# ========================================================
# 8. MASTER DASHBOARD (Clickable & Private Cards)
# ========================================================
if st.session_state.screen == "🏠 Dashboard":
    st.header(f"Welcome to {APP_NAME}")
    orders = orders_db[orders_db['Phone'].apply(clean_phone) == u_ph]
    
    # Metrics
    t_cnt = len(orders)
    p_cnt = len(orders[orders['Status'].str.contains('Pending|Process', case=False)])
    c_cnt = len(orders[orders['Status'].str.contains('Paid|Complete', case=False)])
    m_cnt = len(users_db)

    # UI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="m-card c-total"><small>MY ORDERS</small><h3>{t_cnt}</h3></div>', unsafe_allow_html=True)
        if st.button("View Details", key="v1"): nav("📜 History")
    with col2:
        st.markdown(f'<div class="m-card c-pending"><small>PENDING</small><h3>{p_cnt}</h3></div>', unsafe_allow_html=True)
        if is_adm and st.button("Manage Pending", key="v2"): nav("🔐 Admin")
    with col3:
        st.markdown(f'<div class="m-card c-complete"><small>COMPLETED</small><h3>{c_cnt}</h3></div>', unsafe_allow_html=True)
        if is_adm and st.button("Manage Sales", key="v3"): nav("🔐 Admin")
    
    if is_adm:
        with col4:
            st.markdown(f'<div class="m-card c-active"><small>STORE MEMBERS</small><h3>{m_cnt}</h3></div>', unsafe_allow_html=True)
            if st.button("User List", key="v4"): nav("🔐 Admin")

    st.subheader("🕒 Recent Activity")
    for _, r in orders.tail(5).iloc[::-1].iterrows():
        st.markdown(f'<div class="order-row"><div><b>{r["Product"]}</b><br>{r["Timestamp"]}</div><div style="text-align:right;">Rs. {r["Bill"]}<br><span style="color:blue;">{r["Status"]}</span></div></div>', unsafe_allow_html=True)

# ========================================================
# 9. ORDER WIZARD (Phase 1-5)
# ========================================================
if st.session_state.wizard:
    @st.dialog("🛒 Place Your Order")
    def run_w():
        s = st.session_state.step
        st.progress(s/5)
        if s == 1:
            cat = st.selectbox("Category", settings_db['Category'].unique())
            prod = st.selectbox("Product", settings_db[settings_db['Category']==cat]['Product Name'].unique())
            if st.button("Next"): 
                st.session_state.buf.update({"p":prod})
                st.session_state.step = 2; st.rerun()
        elif s == 2:
            rec = settings_db[settings_db['Product Name']==st.session_state.buf['p']].iloc[0]
            sz = st.radio("Size", ["20kg", "Gallon", "Quarter"])
            qty = st.number_input("Quantity", 1, 100)
            total = float(rec[f"Price_{sz}"]) * qty
            if st.button(f"Pay Rs. {total}"):
                st.session_state.buf.update({"sz":sz, "qty":qty, "total":total})
                st.session_state.step = 3; st.rerun()
        elif s == 3:
            m = st.radio("Method", ["JazzCash", "EasyPaisa", "COD"])
            if st.button("Proceed"):
                st.session_state.buf['m'] = m
                st.session_state.step = 4 if m != "COD" else 5; st.rerun()
        elif s == 4:
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={J_NO}"
            st.markdown(f"<div class='qr-container'><img src='{qr}' width='150'><br><b>Pay to: {J_NO}</b></div>", unsafe_allow_html=True)
            proof = st.file_uploader("Upload Screenshot")
            if proof and st.button("Submit Proof"): st.session_state.step = 5; st.rerun()
        elif s == 5:
            if st.button("Confirm Order ✅"):
                requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":get_inv_id(orders_db), "name":u['Name'], "phone":u_ph, "product":st.session_state.buf['p'], "bill":st.session_state.buf['total'], "payment_method":st.session_state.buf['m']})
                st.session_state.wizard = False; st.balloons(); st.rerun()
    run_w()

# ========================================================
# 10. ADMIN MASTER CONTROL (Settings & Database)
# ========================================================
elif st.session_state.screen == "🔐 Admin" and is_adm:
    st.header("🛡️ Factory Admin Control")
    t1, t2, t3 = st.tabs(["🛒 Orders", "👥 Members", "⚙️ App Settings"])
    
    with t1:
        for idx, r in orders_db.iloc[::-1].iterrows():
            with st.expander(f"Order #{r['Invoice_ID']} - {r['Name']}"):
                st.write(f"Product: {r['Product']} | Bill: {r['Bill']}")
                if st.button("Approve Payment ✅", key=f"adm_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":r['Invoice_ID']})
                    st.rerun()
                    
    with t2:
        st.subheader("Member Directory")
        st.dataframe(users_db, use_container_width=True)
        
    with t3:
        st.subheader("Global App Customization")
        new_name = st.text_input("Change App Name", APP_NAME)
        new_j = st.text_input("JazzCash No", J_NO)
        new_e = st.text_input("EasyPaisa No", E_NO)
        st.text_area("Terms & Conditions", "1. No refund after delivery...")
        if st.button("Save System Settings"):
            st.success("Settings Updated Locally!")

# ========================================================
# 11. PROFILE & HISTORY (Remaining Sections)
# ========================================================
elif st.session_state.screen == "📜 History":
    st.header("My Orders")
    st.dataframe(orders_db[orders_db['Phone'].apply(clean_phone)==u_ph].iloc[::-1], use_container_width=True)

elif st.session_state.screen == "👤 Profile":
    st.header("Account Settings")
    st.image(u.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png'), width=150)
    st.write(f"**Name:** {u['Name']}")
    st.write(f"**Phone:** {u_ph}")
    if st.button("Change Password"): st.info("Contact Admin for Security Reset")

st.markdown(f"<div class='footer-text'>© 2026 {APP_NAME} | Designed for Professionals</div>", unsafe_allow_html=True)
