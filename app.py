import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# 1. DATABASE & CONFIGURATION
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
ADMIN_PH = "03005508112"

# Session State Initialization (No Shortcutting)
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'page' not in st.session_state: st.session_state.page = "🏠 Dashboard"
if 'wizard' not in st.session_state: st.session_state.wizard = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'order_buf' not in st.session_state: st.session_state.order_buf = {}
if 'app_name' not in st.session_state: st.session_state.app_name = "Paint Pro Store"
if 'jc_no' not in st.session_state: st.session_state.jc_no = "03005508112"
if 'ep_no' not in st.session_state: st.session_state.ep_no = "03005508112"
if 'footer_msg' not in st.session_state: st.session_state.footer_msg = "© 2026 Paint Pro Store | All Rights Reserved"

st.set_page_config(page_title=st.session_state.app_name, layout="wide")

# ========================================================
# 2. MASTER CSS (CLICKABLE CARDS & ANIMATIONS)
# ========================================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f1f5f9; font-family: 'Segoe UI', sans-serif; }}
    
    /* Clickable Metric Cards */
    .metric-card-container {{
        position: relative;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        margin-bottom: 25px;
    }}
    .metric-card-container:hover {{ transform: translateY(-12px); }}
    
    .m-card {{
        padding: 45px 25px; border-radius: 30px; text-align: center; color: white;
        min-height: 220px; display: flex; flex-direction: column; justify-content: center;
        box-shadow: 0 15px 35px rgba(0,0,0,0.12); border: 1px solid rgba(255,255,255,0.2);
    }}
    
    .c-blue {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); }}
    .c-gold {{ background: linear-gradient(135deg, #b45309, #fbbf24); }}
    .c-green {{ background: linear-gradient(135deg, #065f46, #10b981); }}
    .c-purple {{ background: linear-gradient(135deg, #5b21b6, #a78bfa); }}

    /* Invisible Button Overlay Technique */
    .stButton>button {{
        width: 100%; height: 220px; background: transparent !important;
        color: transparent !important; border: none !important;
        position: absolute; top: 0; left: 0; z-index: 10; cursor: pointer;
    }}
    .stButton>button:hover {{ background: transparent !important; border: none !important; }}
    .stButton>button:active {{ background: transparent !important; border: none !important; transform: scale(0.98); }}

    /* Layout Elements */
    .custom-row {{
        background: white; padding: 25px; border-radius: 20px; margin-bottom: 15px;
        border-left: 10px solid #1e3a8a; display: flex; justify-content: space-between;
        align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }}
    .footer-section {{
        text-align: center; padding: 60px; color: #64748b; font-size: 14px;
        border-top: 1px solid #e2e8f0; margin-top: 100px;
    }}
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. DATABASE ENGINE (GOOGLE SHEETS SYNC)
# ========================================================
@st.cache_data(ttl=1)
def sync_database():
    try:
        t_stamp = int(time.time())
        base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t_stamp}&sheet="
        users = pd.read_csv(base + "Users").fillna('')
        orders = pd.read_csv(base + "Orders").fillna('')
        settings = pd.read_csv(base + "Settings").fillna('')
        feedback = pd.read_csv(base + "Feedback").fillna('')
        return users, orders, settings, feedback
    except Exception as e:
        st.error(f"Syncing Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

u_db, o_db, s_db, f_db = sync_database()

def clean_mobile(num):
    s = str(num).strip().split('.')[0]
    if s and not s.startswith('0'): return '0' + s
    return s

def nav_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# ========================================================
# 4. AUTHENTICATION (SECURE LOGIN GATEWAY)
# ========================================================
if not st.session_state.auth:
    _, auth_box, _ = st.columns([1, 1.8, 1])
    with auth_box:
        st.markdown(f"<h1 style='text-align:center; color:#1e3a8a;'>🎨 {st.session_state.app_name}</h1>", unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["🔐 Secure Login", "📝 Register Shop"])
        
        with login_tab:
            l_ph = st.text_input("Mobile Number", placeholder="03XXXXXXXXX")
            l_pw = st.text_input("Password", type="password", placeholder="••••••••")
            if st.button("Unlock Dashboard 🚀", use_container_width=True):
                target = clean_mobile(l_ph)
                match = u_db[(u_db['Phone'].apply(clean_mobile) == target) & (u_db['Password'].astype(str) == l_pw)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Authentication Failed! Incorrect Mobile or Password.")
        
        with signup_tab:
            st.info("New shop registration requires admin approval.")
            r_name = st.text_input("Shop/Owner Name")
            r_phone = st.text_input("Contact Number")
            r_pass = st.text_input("Set Password", type="password")
            if st.button("Submit Registration ✨", use_container_width=True):
                if r_name and r_phone and r_pass:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":clean_mobile(r_phone), "password":r_pass})
                    st.success("Application Submitted! Contact Admin for Activation.")
    st.stop()

# ========================================================
# 5. NAVIGATION & USER IDENTITY
# ========================================================
curr_user = st.session_state.user
curr_name = curr_user.get('Name', 'User')
curr_ph = clean_mobile(curr_user.get('Phone', ''))
is_master_admin = (curr_ph == clean_mobile(ADMIN_PH))

with st.sidebar:
    st.markdown(f'''
        <div style="text-align:center; padding: 20px;">
            <img src="{curr_user.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png')}" style="width:120px; border-radius:50%; border:4px solid #1e3a8a;">
            <h2 style="margin-top:15px;">{curr_name}</h2>
            <p style="color:#64748b;">{'⭐ FACTORY OWNER' if is_master_admin else 'VERIFIED SHOP'}</p>
        </div>
    ''', unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Home Dashboard", use_container_width=True): nav_to("🏠 Dashboard")
    if st.button("🛒 Create New Order", use_container_width=True, type="primary"):
        st.session_state.wizard = True; st.session_state.step = 1; st.rerun()
    if st.button("📜 My Transaction History", use_container_width=True): nav_to("📜 History")
    if st.button("👤 Shop Profile", use_container_width=True): nav_to("👤 Profile")
    
    if is_master_admin:
        st.divider(); st.write("🛠️ **ADMIN CONTROLS**")
        if st.button("🔐 Master Admin Panel", use_container_width=True): nav_to("🔐 Admin")
    
    st.divider()
    if st.button("Logout 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()

# ========================================================
# 6. DASHBOARD (CLICKABLE METRICS)
# ========================================================
if st.session_state.page == "🏠 Dashboard":
    st.header(f"Welcome to {st.session_state.app_name}")
    my_orders = o_db[o_db['Phone'].apply(clean_mobile) == curr_ph]
    
    # Grid for Clickable Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card-container"><div class="m-card c-blue"><small>TOTAL BOOKINGS</small><h1>{len(my_orders)}</h1></div></div>', unsafe_allow_html=True)
        if st.button("", key="nav_total"): nav_to("📜 History")
    with c2:
        st.markdown(f'<div class="metric-card-container"><div class="m-card c-gold"><small>PENDING APPROVAL</small><h1>{len(my_orders[my_orders["Status"]=="Pending"])}</h1></div></div>', unsafe_allow_html=True)
        if is_master_admin: 
            if st.button("", key="nav_pending"): nav_to("🔐 Admin")
        else: st.button("", key="nav_pending_u", disabled=True)
    with c3:
        st.markdown(f'<div class="metric-card-container"><div class="m-card c-green"><small>PAID ORDERS</small><h1>{len(my_orders[my_orders["Status"]=="Paid"])}</h1></div></div>', unsafe_allow_html=True)
        if is_master_admin: 
            if st.button("", key="nav_paid"): nav_to("🔐 Admin")
        else: st.button("", key="nav_paid_u", disabled=True)
    if is_master_admin:
        with c4:
            st.markdown(f'<div class="metric-card-container"><div class="m-card c-purple"><small>SYSTEM MEMBERS</small><h1>{len(u_db)}</h1></div></div>', unsafe_allow_html=True)
            if st.button("", key="nav_members"): nav_to("🔐 Admin")

    st.subheader("🕒 Recent Activity")
    for _, r in my_orders.tail(5).iloc[::-1].iterrows():
        st.markdown(f'''
            <div class="custom-row">
                <div><b>{r["Product"]}</b><br><small>{r["Timestamp"]}</small></div>
                <div style="text-align:right;"><b>Rs. {r["Bill"]}</b><br><span style="color:#2563eb;">{r["Status"]}</span></div>
            </div>
        ''', unsafe_allow_html=True)

# ========================================================
# 7. THE MASTER ORDER WIZARD (PHASE 1-5)
# ========================================================
if st.session_state.wizard:
    @st.dialog("🛒 Professional Booking Gateway")
    def run_wizard():
        step = st.session_state.step
        st.progress(step/5)
        st.write(f"Phase {step} of 5")
        
        if step == 1:
            st.subheader("Select Category & Brand")
            cat = st.selectbox("Category", s_db['Category'].unique())
            prod = st.selectbox("Product", s_db[s_db['Category']==cat]['Product Name'].unique())
            if st.button("Proceed to Size ➡️", use_container_width=True):
                st.session_state.order_buf['p'] = prod; st.session_state.step = 2; st.rerun()
        
        elif step == 2:
            st.subheader("Specifications")
            row = s_db[s_db['Product Name']==st.session_state.order_temp.get('p', st.session_state.order_buf['p'])].iloc[0]
            sz = st.radio("Choose Packing", ["20kg", "Gallon", "Quarter"], horizontal=True)
            qty = st.number_input("Enter Quantity", 1, 1000, 1)
            price = float(row[f"Price_{sz}"])
            total = price * qty
            st.markdown(f"<div style='background:#f8fafc; padding:20px; border-radius:15px;'><h3>Total Bill: Rs. {total}</h3></div>", unsafe_allow_html=True)
            if st.button("Confirm Amount ➡️", use_container_width=True):
                st.session_state.order_buf.update({"sz":sz, "qty":qty, "total":total})
                st.session_state.step = 3; st.rerun()

        elif step == 3:
            st.subheader("Payment Gateway")
            met = st.radio("Choose Method", ["JazzCash", "EasyPaisa", "COD"])
            if st.button("Select Method ➡️", use_container_width=True):
                st.session_state.order_buf['m'] = met
                st.session_state.step = 4 if met != "COD" else 5; st.rerun()

        elif step == 4:
            st.subheader("Verification")
            m = st.session_state.order_buf['m']
            num = st.session_state.jc_no if m == "JazzCash" else st.session_state.ep_no
            st.info(f"Send Rs. {st.session_state.order_buf['total']} to {num}")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={num}")
            if st.file_uploader("Upload Payment Screenshot") and st.button("Verified ✅"):
                st.session_state.step = 5; st.rerun()

        elif step == 5:
            st.subheader("Final Submission")
            if st.button("Book Order Now 🚀", type="primary", use_container_width=True):
                requests.post(SCRIPT_URL, json={
                    "action":"order", "name":curr_name, "phone":curr_ph,
                    "product": f"{st.session_state.order_buf['qty']}x {st.session_state.order_buf['p']} ({st.session_state.order_buf['sz']})",
                    "bill": st.session_state.order_buf['total'], "payment_method": st.session_state.order_buf['m']
                })
                st.session_state.wizard = False; st.balloons(); st.rerun()
    run_wizard()

# ========================================================
# 8. MASTER ADMIN & SYSTEM SETTINGS
# ========================================================
elif st.session_state.page == "🔐 Admin" and is_master_admin:
    st.header("🛡️ Factory Control Center")
    adm_t1, adm_t2, adm_t3 = st.tabs(["🛒 Manage Orders", "👥 Users List", "⚙️ App Master Settings"])
    
    with adm_t1:
        for idx, row in o_db.iloc[::-1].iterrows():
            with st.expander(f"Order #{idx} - {row['Name']} ({row['Status']})"):
                st.write(f"Product: {row['Product']} | Bill: Rs. {row['Bill']}")
                if row['Status'] != "Paid":
                    if st.button("Confirm Payment ✅", key=f"p_btn_{idx}"):
                        requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":idx})
                        st.success("Payment Verified!"); time.sleep(1); st.rerun()
    
    with adm_t2: st.dataframe(u_db, use_container_width=True)
    
    with adm_t3:
        st.subheader("🚀 Global Configuration")
        st.session_state.app_name = st.text_input("Application Name", st.session_state.app_name)
        st.session_state.jc_no = st.text_input("JazzCash Merchant Number", st.session_state.jc_no)
        st.session_state.ep_no = st.text_input("EasyPaisa Merchant Number", st.session_state.ep_no)
        st.session_state.footer_msg = st.text_area("Footer Copyright Text", st.session_state.footer_msg)
        if st.button("Apply Changes 💾", type="primary"):
            st.success("App Settings Updated Locally!"); st.rerun()

# ========================================================
# 9. HISTORY & GLOBAL FOOTER
# ========================================================
elif st.session_state.page == "📜 History":
    st.header("Transaction History")
    st.dataframe(o_db[o_db['Phone'].apply(clean_mobile)==curr_ph].iloc[::-1], use_container_width=True)

st.markdown(f"<div class='footer-section'>{st.session_state.footer_msg}</div>", unsafe_allow_html=True)

