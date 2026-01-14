import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# ========================================================
# 1. GLOBAL SYSTEM CONFIGURATION
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
ADMIN_PH = "03005508112"

st.set_page_config(page_title="Paint Pro Master Admin", layout="wide")

# Persistent State Management
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'page' not in st.session_state: st.session_state.page = "🏠 Dashboard"
if 'wizard' not in st.session_state: st.session_state.wizard = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'order_buf' not in st.session_state: st.session_state.order_buf = {}
if 'app_name' not in st.session_state: st.session_state.app_name = "Paint Pro Store"
if 'jc_no' not in st.session_state: st.session_state.jc_no = "03005508112"
if 'ep_no' not in st.session_state: st.session_state.ep_no = "03005508112"

# ========================================================
# 2. ADVANCED CSS (Clickable Cards Logic)
# ========================================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f4f7f6; }}
    .card-wrapper {{ position: relative; margin-bottom: 25px; transition: 0.3s; }}
    .m-card {{
        padding: 40px 20px; border-radius: 25px; text-align: center; color: white;
        min-height: 200px; display: flex; flex-direction: column; justify-content: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.1);
    }}
    .card-wrapper:hover {{ transform: translateY(-8px); filter: brightness(1.1); }}
    .c-total {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); }}
    .c-pending {{ background: linear-gradient(135deg, #b45309, #f59e0b); }}
    .c-complete {{ background: linear-gradient(135deg, #065f46, #10b981); }}
    .c-active {{ background: linear-gradient(135deg, #5b21b6, #8b5cf6); }}
    
    /* Overlay Button: Makes the whole card clickable without showing a button */
    .stButton>button {{
        width: 100%; height: 200px; background: transparent !important;
        color: transparent !important; border: none !important;
        position: absolute; top: 0; left: 0; z-index: 10; cursor: pointer;
    }}
    .stButton>button:hover {{ background: transparent !important; border: none !important; }}
    
    .list-item {{
        background: white; padding: 20px; border-radius: 15px; margin-bottom: 12px;
        border-left: 8px solid #1e3a8a; display: flex; justify-content: space-between;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }}
    .footer-text {{ text-align: center; padding: 40px; color: #94a3b8; font-size: 14px; border-top: 1px solid #e2e8f0; }}
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. DATA & UTILS
# ========================================================
@st.cache_data(ttl=2)
def load_master_data():
    try:
        t = int(time.time())
        u = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet=Users").fillna('')
        o = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet=Orders").fillna('')
        s = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet=Settings").fillna('')
        return u, o, s
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_db, orders_db, settings_db = load_master_data()

def clean_ph(p):
    s = str(p).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def nav(p):
    st.session_state.page = p
    st.rerun()

# ========================================================
# 4. AUTHENTICATION MODULE
# ========================================================
if not st.session_state.auth:
    _, c_col, _ = st.columns([1, 1.5, 1])
    with c_col:
        st.markdown(f"<h1 style='text-align:center;'>{st.session_state.app_name}</h1>", unsafe_allow_html=True)
        with st.container(border=True):
            l_ph = st.text_input("Registered Mobile Number")
            l_pw = st.text_input("Secret Password", type="password")
            if st.button("Access Dashboard 🚀", use_container_width=True):
                target = clean_ph(l_ph)
                match = users_db[(users_db['Phone'].apply(clean_ph) == target) & (users_db['Password'].astype(str) == l_pw)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Login failed. Check details.")
    st.stop()

# ========================================================
# 5. SIDEBAR & NAVIGATION
# ========================================================
u_data = st.session_state.user
u_phone = clean_ph(u_data.get('Phone', ''))
is_admin = (u_phone == clean_ph(ADMIN_PH))

with st.sidebar:
    st.header(u_data.get('Name'))
    st.divider()
    if st.button("🏠 Home", use_container_width=True): nav("🏠 Dashboard")
    if st.button("🛍️ New Order", use_container_width=True, type="primary"):
        st.session_state.wizard = True; st.session_state.step = 1; st.rerun()
    if st.button("📜 My History", use_container_width=True): nav("📜 History")
    if is_admin:
        st.divider(); st.write("🛠️ ADMIN ONLY")
        if st.button("🔐 Master Admin", use_container_width=True): nav("🔐 Admin")
    if st.button("Logout 🚪"): st.session_state.clear(); st.rerun()

# ========================================================
# 6. CLICKABLE DASHBOARD
# ========================================================
if st.session_state.page == "🏠 Dashboard":
    st.header("Factory Command Overview")
    my_o = orders_db[orders_db['Phone'].apply(clean_ph) == u_phone]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="card-wrapper"><div class="m-card c-total"><small>TOTAL</small><h3>{len(my_o)}</h3></div></div>', unsafe_allow_html=True)
        if st.button("", key="dash_1"): nav("📜 History")
    with col2:
        st.markdown(f'<div class="card-wrapper"><div class="m-card c-pending"><small>PENDING</small><h3>{len(my_o[my_o["Status"]=="Pending"])}</h3></div></div>', unsafe_allow_html=True)
        if is_admin: 
            if st.button("", key="dash_2"): nav("🔐 Admin")
    with col3:
        st.markdown(f'<div class="card-wrapper"><div class="m-card c-complete"><small>COMPLETED</small><h3>{len(my_o[my_o["Status"]=="Paid"])}</h3></div></div>', unsafe_allow_html=True)
        if is_admin: 
            if st.button("", key="dash_3"): nav("🔐 Admin")
    if is_admin:
        with col4:
            st.markdown(f'<div class="card-wrapper"><div class="m-card c-active"><small>MEMBERS</small><h3>{len(users_db)}</h3></div></div>', unsafe_allow_html=True)
            if st.button("", key="dash_4"): nav("🔐 Admin")

    st.subheader("Recent Activity")
    for _, r in my_o.tail(5).iloc[::-1].iterrows():
        st.markdown(f'<div class="list-item"><div><b>{r["Product"]}</b><br>{r["Timestamp"]}</div><div style="text-align:right;">Rs. {r["Bill"]}<br>{r["Status"]}</div></div>', unsafe_allow_html=True)

# ========================================================
# 7. 5-STEP ORDER WIZARD
# ========================================================
if st.session_state.wizard:
    @st.dialog("🛒 Professional Booking")
    def run_wizard():
        s = st.session_state.step
        st.progress(s/5)
        if s == 1:
            st.subheader("Step 1: Choose Product")
            cat = st.selectbox("Category", settings_db['Category'].unique())
            prod = st.selectbox("Product", settings_db[settings_db['Category']==cat]['Product Name'].unique())
            if st.button("Next"): st.session_state.order_buf['p'] = prod; st.session_state.step = 2; st.rerun()
        elif s == 2:
            st.subheader("Step 2: Details")
            sz = st.radio("Size", ["20kg", "Gallon", "Quarter"], horizontal=True)
            qty = st.number_input("Quantity", 1, 1000, 1)
            if st.button("Next"): st.session_state.order_buf.update({"sz":sz, "qty":qty}); st.session_state.step = 3; st.rerun()
        elif s == 3:
            st.subheader("Step 3: Payment")
            met = st.radio("Method", ["JazzCash", "EasyPaisa", "COD"])
            if st.button("Next"): st.session_state.order_buf['m'] = met; st.session_state.step = 4 if met != "COD" else 5; st.rerun()
        elif s == 4:
            st.subheader("Step 4: Verify")
            num = st.session_state.jc_no if "Jazz" in st.session_state.order_buf['m'] else st.session_state.ep_no
            st.write(f"Send Payment to: {num}")
            if st.file_uploader("Screenshot") and st.button("Submit"): st.session_state.step = 5; st.rerun()
        elif s == 5:
            st.subheader("Step 5: Review")
            if st.button("Confirm Order 🚀"):
                requests.post(SCRIPT_URL, json={"action":"order", "name":u_data.get('Name'), "phone":u_phone, "product":st.session_state.order_buf['p'], "bill":"5000", "payment_method":st.session_state.order_buf['m']})
                st.session_state.wizard = False; st.rerun()
    run_wizard()

# ========================================================
# 8. ADMIN MASTER CONTROL
# ========================================================
elif st.session_state.page == "🔐 Admin" and is_admin:
    st.header("🛡️ Master Control Dashboard")
    tab1, tab2, tab3 = st.tabs(["🛒 All Orders", "👥 Members", "⚙️ App Settings"])
    
    with tab1:
        for idx, r in orders_db.iloc[::-1].iterrows():
            with st.expander(f"Order #{idx} - {r['Name']}"):
                st.write(f"Item: {r['Product']} | Payment: {r['Payment_Method']}")
                if r['Status'] != "Paid":
                    if st.button("Confirm & Mark Paid ✅", key=f"pay_{idx}"):
                        requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":idx})
                        st.rerun()
    with tab2:
        st.dataframe(users_db, use_container_width=True)
    with tab3:
        st.subheader("Global System Updates")
        st.session_state.app_name = st.text_input("App Name", st.session_state.app_name)
        st.session_state.jc_no = st.text_input("JazzCash Merchant No", st.session_state.jc_no)
        st.session_state.ep_no = st.text_input("EasyPaisa Merchant No", st.session_state.ep_no)
        if st.button("Save App Settings 💾"): st.success("Updated!"); time.sleep(1); st.rerun()

# ========================================================
# 9. HISTORY & FOOTER
# ========================================================
elif st.session_state.page == "📜 History":
    st.header("Your Order History")
    st.dataframe(orders_db[orders_db['Phone'].apply(clean_ph) == u_phone].iloc[::-1], use_container_width=True)

st.markdown(f"<div class='footer-text'>{st.session_state.app_name} | Admin Support: {ADMIN_PH}</div>", unsafe_allow_html=True)
