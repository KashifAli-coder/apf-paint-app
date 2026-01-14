import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# 1. SYSTEM CONFIGURATION & DATABASE
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
ADMIN_PH = "03005508112"

# Default UI Settings (Admin Panel se change hon gi)
if 'app_settings' not in st.session_state:
    st.session_state.app_settings = {
        "name": "Paint Pro Store",
        "jc_no": "03005508112",
        "ep_no": "03005508112",
        "footer": "© 2026 Paint Pro Store | All Rights Reserved",
        "header_color": "#1e3a8a"
    }

st.set_page_config(page_title=st.session_state.app_settings["name"], layout="wide", initial_sidebar_state="expanded")

# ========================================================
# 2. ADVANCED CSS (Clickable Cards & Invisible Buttons)
# ========================================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8fafc; }}
    
    /* Master Card Styling */
    .metric-card-wrapper {{
        position: relative;
        margin-bottom: 20px;
    }}
    .m-card {{
        padding: 30px; border-radius: 25px; text-align: center; color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); transition: 0.4s ease;
        min-height: 180px; display: flex; flex-direction: column; justify-content: center;
    }}
    .m-card:hover {{ transform: translateY(-8px); filter: brightness(1.1); box-shadow: 0 15px 35px rgba(0,0,0,0.2); }}
    
    .c-total {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); }}
    .c-pending {{ background: linear-gradient(135deg, #f59e0b, #fbbf24); }}
    .c-complete {{ background: linear-gradient(135deg, #059669, #10b981); }}
    .c-active {{ background: linear-gradient(135deg, #7c3aed, #a78bfa); }}

    /* Invisible Button Overlay */
    .stButton>button {{
        width: 100%; height: 180px; background: transparent !important;
        color: transparent !important; border: none !important;
        position: absolute; top: 0; left: 0; z-index: 10; cursor: pointer;
    }}
    .stButton>button:hover {{ background: transparent !important; color: transparent !important; border: none !important; }}
    .stButton>button:active {{ background: transparent !important; border: none !important; }}

    /* Order Rows */
    .order-row {{
        background: white; padding: 20px; border-radius: 18px; margin-bottom: 12px;
        border-left: 6px solid {st.session_state.app_settings["header_color"]}; 
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.03);
    }
    
    .footer-box {{
        text-align: center; padding: 50px; color: #94a3b8; font-size: 14px;
        border-top: 1px solid #e2e8f0; margin-top: 60px;
    }}
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. CORE DATA ENGINE
# ========================================================
@st.cache_data(ttl=2)
def load_full_database():
    try:
        ts = int(time.time())
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={ts}&sheet="
        u = pd.read_csv(url + "Users").fillna('')
        s = pd.read_csv(url + "Settings").fillna('')
        o = pd.read_csv(url + "Orders").fillna('')
        f = pd.read_csv(url + "Feedback").fillna('')
        return u, s, o, f
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_db, settings_db, orders_db, feedback_db = load_full_database()

def clean_phone(p):
    s = str(p).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def get_new_inv(df):
    if df.empty or 'Invoice_ID' not in df.columns: return "0001"
    try:
        m = pd.to_numeric(df['Invoice_ID'], errors='coerce').max()
        return f"{int(m) + 1:04d}" if not pd.isna(m) else "0001"
    except: return "0001"

# ========================================================
# 4. SESSION CONTROLLER
# ========================================================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'page' not in st.session_state: st.session_state.page = "🏠 Dashboard"
if 'wizard' not in st.session_state: st.session_state.wizard = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'buf' not in st.session_state: st.session_state.buf = {}
if 'admin_sub_tab' not in st.session_state: st.session_state.admin_sub_tab = 0

def nav(page_name, tab_idx=0):
    st.session_state.page = page_name
    st.session_state.admin_sub_tab = tab_idx
    st.rerun()

# ========================================================
# 5. AUTHENTICATION MODULE
# ========================================================
if not st.session_state.auth:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(f"<h1 style='text-align:center;'>🎨 {st.session_state.app_settings['name']}</h1>", unsafe_allow_html=True)
        t_l, t_r = st.tabs(["🔐 Secure Login", "📝 Member Registration"])
        
        with t_l:
            l_ph = st.text_input("Mobile No", key="l_ph")
            l_pw = st.text_input("Password", type="password", key="l_pw")
            if st.button("Enter Factory Portal 🚀", use_container_width=True):
                target_ph = clean_phone(l_ph)
                match = users_db[(users_db['Phone'].apply(clean_phone) == target_ph) & (users_db['Password'].astype(str) == l_pw)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("❌ Phone or Password incorrect.")
        
        with t_r:
            st.info("Direct registration for new customers.")
            r_n = st.text_input("Full Name")
            r_p = st.text_input("Mobile Number")
            r_w = st.text_input("Set Password", type="password")
            if st.button("Register Now ✨", use_container_width=True):
                if r_n and r_p and r_w:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":r_n, "phone":clean_phone(r_p), "password":r_w})
                    st.success("✅ Application Sent!")
    st.stop()

# ========================================================
# 6. SIDEBAR & IDENTITY
# ========================================================
curr_u = st.session_state.user
u_name, u_phone = curr_u.get('Name', 'User'), clean_phone(curr_u.get('Phone', ''))
is_admin = (u_phone == clean_phone(ADMIN_PH))

with st.sidebar:
    st.markdown(f'''
        <div style="text-align:center; padding: 20px;">
            <img src="{curr_u.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png')}" style="width:120px; border-radius:50%; border:4px solid #3b82f6;">
            <h2 style="margin-top:10px;">{u_name}</h2>
            <p style="color:#64748b;">{'⭐ FACTORY ADMIN' if is_admin else 'C-MEMBER'}</p>
        </div>
    ''', unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Factory Dashboard", use_container_width=True): nav("🏠 Dashboard")
    if st.button("🛍️ Create New Order", use_container_width=True, type="primary"):
        st.session_state.wizard = True
        st.session_state.step = 1
        st.rerun()
    if st.button("📜 My Order History", use_container_width=True): nav("📜 History")
    if st.button("👤 Profile & Safety", use_container_width=True): nav("👤 Profile")
    if st.button("💬 Feedback", use_container_width=True): nav("💬 Feedback")
    
    if is_admin:
        st.divider()
        st.write("🛠️ **MASTER CONTROLS**")
        if st.button("🔐 Master Admin Panel", use_container_width=True): nav("🔐 Admin")
    
    st.divider()
    if st.button("Log Out 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()

# ========================================================
# 7. CLICKABLE DASHBOARD CARDS
# ========================================================
if st.session_state.page == "🏠 Dashboard":
    st.markdown(f"## 🏭 {st.session_state.app_settings['name']} Overview")
    user_orders = orders_db[orders_db['Phone'].apply(clean_phone) == u_phone]
    
    # Logic for metrics
    t_my = len(user_orders)
    p_my = len(user_orders[user_orders['Status'].str.contains('Pending|Process', case=False)])
    c_my = len(user_orders[user_orders['Status'].str.contains('Paid|Complete', case=False)])
    all_users_count = len(users_db)

    # UI Design for Clickable Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="metric-card-wrapper"><div class="m-card c-total"><small>MY TOTAL</small><h3>{t_my}</h3></div></div>', unsafe_allow_html=True)
        if st.button("", key="c_total"): nav("📜 History")
    
    with col2:
        st.markdown(f'<div class="metric-card-wrapper"><div class="m-card c-pending"><small>PENDING</small><h3>{p_my}</h3></div></div>', unsafe_allow_html=True)
        if is_admin:
            if st.button("", key="c_pending"): nav("🔐 Admin", 0)
        else: st.button("", key="c_pending_u", disabled=True)
            
    with col3:
        st.markdown(f'<div class="metric-card-wrapper"><div class="m-card c-complete"><small>COMPLETED</small><h3>{c_my}</h3></div></div>', unsafe_allow_html=True)
        if is_admin:
            if st.button("", key="c_complete"): nav("🔐 Admin", 0)
        else: st.button("", key="c_complete_u", disabled=True)

    if is_admin:
        with col4:
            st.markdown(f'<div class="metric-card-wrapper"><div class="m-card c-active"><small>STORE MEMBERS</small><h3>{all_users_count}</h3></div></div>', unsafe_allow_html=True)
            if st.button("", key="c_active"): nav("🔐 Admin", 1)

    st.subheader("🕒 Recent Transactions")
    if not user_orders.empty:
        for _, r in user_orders.tail(5).iloc[::-1].iterrows():
            st.markdown(f'''
                <div class="order-row">
                    <div><b>{r["Product"]}</b><br><small>{r["Timestamp"]}</small></div>
                    <div style="text-align:right;"><b>Rs. {r["Bill"]}</b><br><span style="color:#2563eb;">{r["Status"]}</span></div>
                </div>
            ''', unsafe_allow_html=True)
    else: st.info("Abhi tak koi order record nahi hai.")

# ========================================================
# 8. THE ORDER WIZARD (Phase 1-5)
# ========================================================
if st.session_state.wizard:
    @st.dialog("🛒 Order Booking Gateway")
    def run_full_wizard():
        step = st.session_state.step
        st.progress(step/5)
        st.write(f"Step {step} of 5")
        
        if step == 1:
            st.subheader("Select Category & Product")
            cats = settings_db['Category'].unique()
            s_cat = st.selectbox("Category", cats)
            prods = settings_db[settings_db['Category']==s_cat]['Product Name'].unique()
            s_prod = st.selectbox("Product Name", prods)
            if st.button("Next: Choose Size ➡️"):
                st.session_state.buf.update({"p": s_prod})
                st.session_state.step = 2; st.rerun()
                
        elif step == 2:
            st.subheader("Specifications")
            p_rec = settings_db[settings_db['Product Name'] == st.session_state.buf['p']].iloc[0]
            sz = st.radio("Select Packing", ["20kg", "Gallon", "Quarter"], horizontal=True)
            qty = st.number_input("Enter Quantity", 1, 5000, 1)
            price = float(p_rec.get(f"Price_{sz}", 0))
            total = price * qty
            st.info(f"💰 Total Amount to Pay: Rs. {total}")
            if st.button("Next: Payment Method ➡️"):
                st.session_state.buf.update({"sz":sz, "qty":qty, "total":total})
                st.session_state.step = 3; st.rerun()

        elif step == 3:
            st.subheader("Select Payment Method")
            met = st.radio("Choose Method", ["JazzCash", "EasyPaisa", "COD"])
            st.warning("Digital payment ke liye PIN flash message tab hi aayega jab aap payment verify karenge.")
            if st.button("Proceed to Pay ➡️"):
                st.session_state.buf['met'] = met
                st.session_state.step = 4 if met != "COD" else 5; st.rerun()

        elif step == 4:
            st.subheader("Final Verification")
            met = st.session_state.buf['met']
            num = st.session_state.app_settings['jc_no'] if met == "JazzCash" else st.session_state.app_settings['ep_no']
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={num}"
            st.markdown(f'''
                <div style="text-align:center; background:white; padding:20px; border-radius:20px; border:2px dashed #3b82f6;">
                    <img src="{qr}" width="160"><br>
                    <b>Account Number: {num}</b><br>
                    <h2>Amount: Rs. {st.session_state.buf['total']}</h2>
                </div>
            ''', unsafe_allow_html=True)
            proof = st.file_uploader("Upload Transaction Screenshot (Proof)", type=['jpg','png','jpeg'])
            if proof and st.button("Verify & Submit ✅"):
                st.session_state.step = 5; st.rerun()

        elif step == 5:
            st.subheader("Review Order Details")
            d = st.session_state.buf
            st.write(f"Product: {d['p']} ({d['sz']})")
            st.write(f"Total Bill: Rs. {d['total']}")
            st.write(f"Method: {d['met']}")
            if st.button("Final Submission 🚀", type="primary", use_container_width=True):
                inv = get_new_inv(orders_db)
                requests.post(SCRIPT_URL, json={
                    "action":"order", "invoice_id":inv, "name":u_name, "phone":u_phone,
                    "product": f"{d['qty']}x {d['p']} ({d['sz']})", "bill":d['total'], "payment_method":d['met']
                })
                st.session_state.wizard = False; st.balloons(); st.rerun()
    run_full_wizard()

# ========================================================
# 9. ADMIN PANEL (With All Tabs)
# ========================================================
elif st.session_state.page == "🔐 Admin" and is_admin:
    st.header("🛡️ Factory Control Center")
    a_t1, a_t2, a_t3, a_t4 = st.tabs(["🛒 Orders", "👥 Members", "⚙️ App Master Settings", "💬 Feedback"])
    
    with a_t1:
        st.subheader("Manage All System Orders")
        for idx, r in orders_db.iloc[::-1].iterrows():
            with st.expander(f"Order #{r['Invoice_ID']} - {r['Name']} ({r['Status']})"):
                st.write(f"**Item:** {r['Product']}")
                st.write(f"**Bill:** Rs. {r['Bill']} | **Method:** {r['Payment_Method']}")
                if r['Status'] != "Paid":
                    if st.button("Verify & Mark Paid ✅", key=f"pay_adm_{idx}"):
                        requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":r['Invoice_ID']})
                        st.success("Order Approved!"); time.sleep(1); st.rerun()

    with a_t2:
        st.subheader("Registered Users Database")
        st.dataframe(users_db, use_container_width=True, hide_index=True)
        
    with a_t3:
        st.subheader("🚀 Global App Configuration")
        st.write("In settings se poori app ka look aur numbers badal jayen ge.")
        n_name = st.text_input("Application Name", st.session_state.app_settings['name'])
        n_jc = st.text_input("JazzCash Merchant No", st.session_state.app_settings['jc_no'])
        n_ep = st.text_input("EasyPaisa Merchant No", st.session_state.app_settings['ep_no'])
        n_footer = st.text_area("Footer Text", st.session_state.app_settings['footer'])
        
        if st.button("Apply Global Changes 💾"):
            st.session_state.app_settings.update({"name": n_name, "jc_no": n_jc, "ep_no": n_ep, "footer": n_footer})
            st.success("App Settings Updated Locally!"); st.rerun()

    with a_t4:
        st.subheader("User Feedbacks")
        st.dataframe(feedback_db, use_container_width=True)

# ========================================================
# 10. HISTORY, PROFILE & FOOTER
# ========================================================
elif st.session_state.page == "📜 History":
    st.header("📜 Order History")
    h = orders_db[orders_db['Phone'].apply(clean_phone) == u_phone]
    st.dataframe(h.iloc[::-1], use_container_width=True, hide_index=True)

elif st.session_state.page == "👤 Profile":
    st.header("👤 Account Management")
    c1, c2 = st.columns([1, 2])
    with c1: st.image(curr_u.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png'), width=180)
    with c2:
        st.write(f"**User Name:** {u_name}")
        st.write(f"**User Phone:** {u_phone}")
        with st.expander("Security: Update Password"):
            new_p = st.text_input("New Password", type="password")
            if st.button("Update Now"):
                requests.post(SCRIPT_URL, json={"action":"update_password", "phone":u_phone, "password":new_p})
                st.success("Done!"); time.sleep(1); st.rerun()

elif st.session_state.page == "💬 Feedback":
    st.header("💬 Feedback")
    f_msg = st.text_area("Hamein batayein hum apni service kaise behtar kar saktay hain?")
    if st.button("Send Feedback"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":u_phone, "message":f_msg})
        st.success("Thank you for your feedback!"); time.sleep(1); nav("🏠 Dashboard")

# FOOTER
st.markdown(f'<div class="footer-box">{st.session_state.app_settings["footer"]}</div>', unsafe_allow_html=True)
