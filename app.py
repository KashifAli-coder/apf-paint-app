import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# 1. SYSTEM CONFIG & DATABASE CONNECTION
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
ADMIN_PH = "03005508112"  # Sirf is number ko Member card aur Admin settings dikhain gi

st.set_page_config(page_title="Paint Pro Store - Master System", layout="wide", initial_sidebar_state="expanded")

# ========================================================
# 2. DESIGN & STYLING (CSS)
# ========================================================
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .metric-container { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 25px; }
    .m-card {
        flex: 1; min-width: 220px; padding: 25px; border-radius: 20px; text-align: center; color: white;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08); transition: 0.3s; cursor: pointer;
    }
    .m-card:hover { transform: translateY(-5px); box-shadow: 0 12px 24px rgba(0,0,0,0.15); }
    .c-total { background: linear-gradient(135deg, #1e3a8a, #3b82f6); }
    .c-pending { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
    .c-complete { background: linear-gradient(135deg, #059669, #10b981); }
    .c-active { background: linear-gradient(135deg, #7c3aed, #a78bfa); }
    
    .stButton>button { border-radius: 12px; font-weight: 700; height: 3em; transition: 0.3s; }
    .order-row {
        background: white; padding: 20px; border-radius: 15px; margin-bottom: 12px;
        border-left: 6px solid #3b82f6; display: flex; justify-content: space-between;
        align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .footer-box { text-align: center; padding: 40px; color: #94a3b8; font-size: 14px; margin-top: 50px; border-top: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. CORE DATA ENGINE
# ========================================================
@st.cache_data(ttl=2)
def load_all_data():
    try:
        t_stamp = int(time.time())
        base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t_stamp}&sheet="
        u_df = pd.read_csv(base_url + "Users").fillna('')
        s_df = pd.read_csv(base_url + "Settings").fillna('')
        o_df = pd.read_csv(base_url + "Orders").fillna('')
        f_df = pd.read_csv(base_url + "Feedback").fillna('')
        return u_df, s_df, o_df, f_df
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_db, settings_db, orders_db, feedback_db = load_all_data()

def clean_phone(p):
    s = str(p).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def get_next_id(df):
    if df.empty or 'Invoice_ID' not in df.columns: return "0001"
    try:
        max_v = pd.to_numeric(df['Invoice_ID'], errors='coerce').max()
        return f"{int(max_v) + 1:04d}" if not pd.isna(max_v) else "0001"
    except: return "0001"

# ========================================================
# 4. SESSION MANAGEMENT
# ========================================================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'page' not in st.session_state: st.session_state.page = "🏠 Dashboard"
if 'wizard' not in st.session_state: st.session_state.wizard = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'order_buf' not in st.session_state: st.session_state.order_buf = {}
if 'admin_tab_target' not in st.session_state: st.session_state.admin_tab_target = 0

def navigate(p, tab_idx=0):
    st.session_state.page = p
    st.session_state.admin_tab_target = tab_idx
    st.rerun()

# ========================================================
# 5. AUTHENTICATION (Login / Signup)
# ========================================================
if not st.session_state.auth:
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🎨 Paint Pro Store</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Secure Login", "📝 Register Account"])
        with t1:
            l_ph = st.text_input("Mobile Number")
            l_pw = st.text_input("Password", type="password")
            if st.button("Enter Dashboard 🚀", use_container_width=True):
                target = clean_phone(l_ph)
                match = users_db[(users_db['Phone'].apply(clean_phone) == target) & (users_db['Password'].astype(str) == l_pw)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("❌ Invalid Phone or Password!")
        with t2:
            st.info("Fill your details for factory approval.")
            r_n = st.text_input("Full Name")
            r_p = st.text_input("Phone Number")
            r_pass = st.text_input("New Password", type="password")
            if st.button("Create Account ✨", use_container_width=True):
                if r_n and r_p and r_pass:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":r_n, "phone":clean_phone(r_p), "password":r_pass})
                    st.success("✅ Registration Sent to Admin!")
    st.stop()

# ========================================================
# 6. SIDEBAR & NAVIGATION
# ========================================================
curr_user = st.session_state.user
u_name = curr_user.get('Name', 'User')
u_phone = clean_phone(curr_user.get('Phone', ''))
is_admin = (u_phone == clean_phone(ADMIN_PH))

with st.sidebar:
    st.markdown(f'''
        <div style="text-align:center; padding: 10px;">
            <img src="{curr_user.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png')}" style="width:110px; border-radius:50%; border:3px solid #3b82f6;">
            <h3 style="margin-top:10px;">{u_name}</h3>
            <span style="background:#e0f2fe; color:#0369a1; padding:2px 10px; border-radius:10px; font-size:12px;">{'ADMIN ACCESS' if is_admin else 'CUSTOMER'}</span>
        </div>
    ''', unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Home Dashboard", use_container_width=True): navigate("🏠 Dashboard")
    if st.button("🛒 Create New Order", use_container_width=True, type="primary"): 
        st.session_state.wizard = True
        st.session_state.step = 1
        st.rerun()
    if st.button("📜 My Order History", use_container_width=True): navigate("📜 History")
    if st.button("👤 My Profile", use_container_width=True): navigate("👤 Profile")
    
    if is_admin:
        st.divider()
        st.write("🛠️ **ADMIN CONTROLS**")
        if st.button("🔐 Factory Manager", use_container_width=True): navigate("🔐 Admin")
        
    st.divider()
    if st.button("Logout 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()

# ========================================================
# 7. DASHBOARD (Clickable & Dynamic Cards)
# ========================================================
if st.session_state.page == "🏠 Dashboard":
    st.markdown(f"## 🏭 Paint Pro Dashboard")
    my_orders = orders_db[orders_db['Phone'].apply(clean_phone) == u_phone]
    
    # Counts
    total_my = len(my_orders)
    pending_my = len(my_orders[my_orders['Status'].str.contains('Pending|Process', case=False)])
    complete_my = len(my_orders[my_orders['Status'].str.contains('Paid|Complete', case=False)])
    all_members = len(users_db)

    # UI Cards Layout
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="m-card c-total"><small>TOTAL ORDERS</small><h3>{total_my}</h3></div>', unsafe_allow_html=True)
        if st.button("View Records", key="d1", use_container_width=True): navigate("📜 History")
    
    with col2:
        st.markdown(f'<div class="m-card c-pending"><small>PENDING</small><h3>{pending_my}</h3></div>', unsafe_allow_html=True)
        if is_admin:
            if st.button("Approve Pending", key="d2", use_container_width=True): navigate("🔐 Admin", 0)
        else: st.button("Check Status", key="d2_u", use_container_width=True, disabled=True)
            
    with col3:
        st.markdown(f'<div class="m-card c-complete"><small>COMPLETED</small><h3>{complete_my}</h3></div>', unsafe_allow_html=True)
        if is_admin:
            if st.button("View History", key="d3", use_container_width=True): navigate("🔐 Admin", 0)
        else: st.button("Success List", key="d3_u", use_container_width=True, disabled=True)

    if is_admin:
        with col4:
            st.markdown(f'<div class="m-card c-active"><small>STORE MEMBERS</small><h3>{all_members}</h3></div>', unsafe_allow_html=True)
            if st.button("Member List", key="d4", use_container_width=True): navigate("🔐 Admin", 1)

    st.subheader("🕒 Recent Activity")
    if not my_orders.empty:
        for _, r in my_orders.tail(5).iloc[::-1].iterrows():
            st.markdown(f'''
                <div class="order-row">
                    <div><b>{r["Product"]}</b><br><small>{r["Timestamp"]}</small></div>
                    <div style="text-align:right;"><b>Rs. {r["Bill"]}</b><br><span style="color:#2563eb;">{r["Status"]}</span></div>
                </div>
            ''', unsafe_allow_html=True)
    else: st.info("Abhi tak aapka koi order record nahi kiya gaya.")

# ========================================================
# 8. PROFESSIONAL ORDER WIZARD (Phase 1-5)
# ========================================================
if st.session_state.wizard:
    @st.dialog("🛒 New Order Booking")
    def run_paint_wizard():
        step = st.session_state.step
        st.progress(step/5)
        
        if step == 1:
            st.subheader("Select Product")
            cat = st.selectbox("Category", settings_db['Category'].unique())
            prods = settings_db[settings_db['Category']==cat]['Product Name'].unique()
            sel_p = st.selectbox("Product", prods)
            if st.button("Next: Specs ➡️"):
                st.session_state.order_buf.update({"p": sel_p})
                st.session_state.step = 2; st.rerun()
        
        elif step == 2:
            st.subheader("Select Size & Qty")
            p_rec = settings_db[settings_db['Product Name'] == st.session_state.order_buf['p']].iloc[0]
            sz = st.radio("Size", ["20kg", "Gallon", "Quarter"], horizontal=True)
            qty = st.number_input("Quantity", 1, 1000, 1)
            prc = float(p_rec.get(f"Price_{sz}", 0))
            total = prc * qty
            st.markdown(f"### Total Amount: **Rs. {total}**")
            if st.button("Next: Payment ➡️"):
                st.session_state.order_buf.update({"sz":sz, "qty":qty, "total":total})
                st.session_state.step = 3; st.rerun()

        elif step == 3:
            st.subheader("Payment Method")
            met = st.radio("How will you pay?", ["JazzCash", "EasyPaisa", "COD"])
            if st.button("Confirm Method"):
                st.session_state.order_buf['met'] = met
                st.session_state.step = 4 if met != "COD" else 5; st.rerun()

        elif step == 4:
            st.subheader("Confirm Payment")
            met = st.session_state.order_buf['met']
            num = "03005508112"
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={num}"
            st.markdown(f'''
                <div style="text-align:center; background:white; padding:20px; border-radius:20px; border:2px dashed #3b82f6;">
                    <img src="{qr}" width="150"><br>
                    <b>Send Rs. {st.session_state.order_buf['total']} to {num}</b><br>
                    <small>Scan QR code or send manually</small>
                </div>
            ''', unsafe_allow_html=True)
            proof = st.file_uploader("Upload Transaction Screenshot", type=['jpg','png'])
            if proof and st.button("Verify & Submit ✅"):
                st.session_state.step = 5; st.rerun()

        elif step == 5:
            st.subheader("Review & Finalize")
            data = st.session_state.order_buf
            st.write(f"Product: {data['p']} ({data['sz']})")
            st.write(f"Quantity: {data['qty']}")
            st.write(f"Payment: {data['met']}")
            if st.button("Submit My Order 🚀", use_container_width=True, type="primary"):
                inv_id = get_next_id(orders_db)
                requests.post(SCRIPT_URL, json={
                    "action":"order", "invoice_id":inv_id, "name":u_name, "phone":u_phone,
                    "product": f"{data['qty']}x {data['p']} ({data['sz']})", 
                    "bill":data['total'], "payment_method":data['met']
                })
                st.session_state.wizard = False; st.balloons(); st.rerun()
    run_paint_wizard()

# ========================================================
# 9. ADMIN PANEL (Full Authority)
# ========================================================
elif st.session_state.page == "🔐 Admin" and is_admin:
    st.header("🛡️ Factory Admin Control")
    at1, at2, at3 = st.tabs(["🛒 Orders Management", "👥 User Database", "⚙️ Master App Settings"])
    
    with at1:
        st.subheader("Recent System Orders")
        for idx, r in orders_db.iloc[::-1].iterrows():
            with st.expander(f"Invoice #{r['Invoice_ID']} - {r['Name']} ({r['Status']})"):
                st.write(f"**Item:** {r['Product']}")
                st.write(f"**Amount:** Rs. {r['Bill']} | **Method:** {r['Payment_Method']}")
                if r['Status'] != "Paid":
                    if st.button("Confirm Receipt & Mark Paid ✅", key=f"adm_pay_{idx}"):
                        requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":r['Invoice_ID']})
                        st.success("Payment Verified!"); time.sleep(1); st.rerun()

    with at2:
        st.subheader("Member List & Permissions")
        st.dataframe(users_db, use_container_width=True, hide_index=True)
        
    with at3:
        st.subheader("Global App Customization")
        st.info("In settings ko tabdeel karne se poori app ka interface badal jayega.")
        a_name = st.text_input("App Title", "Paint Pro Store")
        a_jc = st.text_input("JazzCash Number", "03005508112")
        a_ep = st.text_input("EasyPaisa Number", "03005508112")
        a_footer = st.text_area("Header/Footer Notes", "© 2026 Paint Pro Store. All Rights Reserved.")
        if st.button("Save System Changes 💾"):
            st.success("Local Settings Updated!")

# ========================================================
# 10. HISTORY, PROFILE & FOOTER
# ========================================================
elif st.session_state.page == "📜 History":
    st.header("📜 Order History")
    hist = orders_db[orders_db['Phone'].apply(clean_phone) == u_phone]
    st.dataframe(hist.iloc[::-1], use_container_width=True, hide_index=True)

elif st.session_state.page == "👤 Profile":
    st.header("👤 Account Settings")
    c1, c2 = st.columns([1, 2])
    with c1: st.image(curr_user.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png'), width=200)
    with c2:
        st.write(f"**Full Name:** {u_name}")
        st.write(f"**Registered Phone:** {u_phone}")
        with st.expander("Security: Change Password"):
            new_pass = st.text_input("New Password", type="password")
            if st.button("Update Password"):
                requests.post(SCRIPT_URL, json={"action":"update_password", "phone":u_phone, "password":new_pass})
                st.success("Password Updated!"); time.sleep(1); st.rerun()

# FOOTER
st.markdown(f'<div class="footer-box">© 2026 Paint Pro Store | System Admin: {ADMIN_PH}</div>', unsafe_allow_html=True)
