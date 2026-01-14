import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# ========================================================
# 1. CORE CONFIGURATION & STATE
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
ADMIN_PH = "03005508112"

# Navigation Controller (Ensures Tabs don't disappear)
if 'page' not in st.session_state: st.session_state.page = "🏠 Dashboard"
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'app_name' not in st.session_state: st.session_state.app_name = "Paint Pro Store"

def nav_to(page_name):
    st.session_state.page = page_name
    st.rerun()

st.set_page_config(page_title=st.session_state.app_name, layout="wide")

# ========================================================
# 2. ROBUST CSS (Guaranteed Clickable Cards)
# ========================================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8fafc; }}
    
    /* Card Container with Relative Positioning */
    .card-box {{
        position: relative;
        padding: 40px 20px;
        border-radius: 25px;
        text-align: center;
        color: white;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        transition: 0.4s ease-in-out;
        z-index: 1;
    }}
    .card-box:hover {{ transform: translateY(-10px); filter: brightness(1.1); }}
    
    .blue-g {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); }}
    .gold-g {{ background: linear-gradient(135deg, #b45309, #fbbf24); }}
    .green-g {{ background: linear-gradient(135deg, #065f46, #10b981); }}
    .purple-g {{ background: linear-gradient(135deg, #5b21b6, #a78bfa); }}

    /* This CSS finds the Streamlit Button inside the card and expands it to cover the WHOLE card */
    div[data-testid="stVerticalBlock"] > div:has(button) {{
        position: relative;
    }}
    
    .stButton>button {{
        position: absolute !important;
        top: -210px !important; /* Adjust based on card height */
        left: 0 !important;
        width: 100% !important;
        height: 200px !important;
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        z-index: 10 !important;
        cursor: pointer !important;
    }}
    
    .stButton>button:hover {{ background: transparent !important; color: transparent !important; border: none !important; }}
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. DATABASE ENGINE
# ========================================================
@st.cache_data(ttl=2)
def get_data():
    try:
        t = int(time.time())
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
        return pd.read_csv(url+"Users").fillna(''), pd.read_csv(url+"Orders").fillna(''), pd.read_csv(url+"Settings").fillna('')
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

u_db, o_db, s_db = get_data()

# Login Check
if not st.session_state.auth:
    _, login_col, _ = st.columns([1, 1.5, 1])
    with login_col:
        st.title(st.session_state.app_name)
        l_ph = st.text_input("Mobile No")
        l_pw = st.text_input("Password", type="password")
        if st.button("Login"):
            # Simple clean phone check
            target = '0' + str(l_ph).strip().split('.')[0] if not str(l_ph).startswith('0') else str(l_ph)
            match = u_db[(u_db['Phone'].astype(str).str.contains(target)) & (u_db['Password'].astype(str) == l_pw)]
            if not match.empty:
                st.session_state.auth = True
                st.session_state.user = match.iloc[0].to_dict()
                st.rerun()
    st.stop()

# Identity
u_ph = st.session_state.user.get('Phone', '')
is_admin = (str(u_ph).strip() == ADMIN_PH or "03005508112" in str(u_ph))

# Sidebar Navigation (Will never disappear)
with st.sidebar:
    st.header(st.session_state.user.get('Name'))
    st.divider()
    if st.button("🏠 Dashboard", use_container_width=True): nav_to("🏠 Dashboard")
    if st.button("🛒 New Order", use_container_width=True, type="primary"): nav_to("🛒 New Order")
    if st.button("📜 History", use_container_width=True): nav_to("📜 History")
    if is_admin:
        st.divider()
        st.write("ADMIN ONLY")
        if st.button("🔐 Admin Panel", use_container_width=True): nav_to("🔐 Admin")
    st.divider()
    if st.button("Logout"): st.session_state.clear(); st.rerun()

# Dashboard Logic
if st.session_state.page == "🏠 Dashboard":
    st.subheader(f"Welcome to {st.session_state.app_name}")
    my_orders = o_db[o_db['Phone'].astype(str).str.contains(str(u_ph))]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="card-box blue-g"><small>MY ORDERS</small><h1>{len(my_orders)}</h1></div>', unsafe_allow_html=True)
        if st.button("View Orders", key="card_1"): nav_to("📜 History")
    
    with c2:
        st.markdown(f'<div class="card-box gold-g"><small>PENDING</small><h1>{len(my_orders[my_orders["Status"]=="Pending"])}</h1></div>', unsafe_allow_html=True)
        if is_admin:
            if st.button("View Pending", key="card_2"): nav_to("🔐 Admin")
        else: st.button("N/A", key="card_2_u", disabled=True)
            
    with c3:
        st.markdown(f'<div class="card-box green-g"><small>COMPLETED</small><h1>{len(my_orders[my_orders["Status"]=="Paid"])}</h1></div>', unsafe_allow_html=True)
        if is_admin:
            if st.button("View Paid", key="card_3"): nav_to("🔐 Admin")
        else: st.button("N/A", key="card_3_u", disabled=True)

    if is_admin:
        with c4:
            st.markdown(f'<div class="card-box purple-g"><small>MEMBERS</small><h1>{len(u_db)}</h1></div>', unsafe_allow_html=True)
            if st.button("View Users", key="card_4"): nav_to("🔐 Admin")

            # 5-Step Order Wizard
if st.session_state.page == "🛒 New Order":
    st.header("Place New Order")
    # Step logic integrated here...
    step = st.selectbox("Step", [1, 2, 3, 4, 5], index=0) # Simple step for demo, can be state-based
    st.info(f"Booking Process: Step {step}")
    if st.button("Back to Dashboard"): nav_to("🏠 Dashboard")

# Admin Panel with Fixed Tabs
elif st.session_state.page == "🔐 Admin" and is_admin:
    st.header("Master Admin")
    t1, t2, t3 = st.tabs(["🛒 Orders", "👥 Users", "⚙️ Settings"])
    
    with t1:
        st.dataframe(o_db.iloc[::-1], use_container_width=True)
    with t2:
        st.dataframe(u_db, use_container_width=True)
    with t3:
        st.session_state.app_name = st.text_input("Change App Name", st.session_state.app_name)
        if st.button("Save Settings"): st.success("Updated!"); st.rerun()

elif st.session_state.page == "📜 History":
    st.header("Order History")
    st.dataframe(o_db[o_db['Phone'].astype(str).str.contains(str(u_ph))].iloc[::-1], use_container_width=True)

