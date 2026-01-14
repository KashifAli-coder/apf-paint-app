import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# 1. DATABASE & SYSTEM INITIALIZATION
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
ADMIN_PH = "03005508112"

# Initializing Master App Settings in Session State
if 'app_master' not in st.session_state:
    st.session_state.app_master = {
        "app_name": "Paint Pro Store",
        "admin_email": "admin@paintpro.com",
        "admin_no": "03005508112",
        "jc_no": "03005508112",
        "ep_no": "03005508112",
        "footer_text": "© 2026 Paint Pro Store | All Rights Reserved",
        "terms": "1. All orders are subject to approval. 2. Payments must be verified via screenshot."
    }

st.set_page_config(
    page_title=st.session_state.app_master["app_name"], 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ========================================================
# 2. ADVANCED UI CUSTOMIZATION (CSS)
# ========================================================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f0f2f6; }}
    
    /* Clickable Card Container */
    .metric-card-wrapper {{
        position: relative;
        margin-bottom: 25px;
        transition: 0.3s;
    }}
    
    .m-card {{
        padding: 40px 20px; border-radius: 25px; text-align: center; color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); 
        min-height: 200px; display: flex; flex-direction: column; justify-content: center;
        border: 2px solid rgba(255,255,255,0.1);
    }}
    .m-card:hover {{ transform: translateY(-10px); filter: brightness(1.1); box-shadow: 0 20px 40px rgba(0,0,0,0.2); }}
    
    .c-total {{ background: linear-gradient(135deg, #0f172a, #334155); }}
    .c-pending {{ background: linear-gradient(135deg, #b45309, #f59e0b); }}
    .c-complete {{ background: linear-gradient(135deg, #065f46, #10b981); }}
    .c-active {{ background: linear-gradient(135deg, #5b21b6, #8b5cf6); }}

    /* Invisible Overlay Button - This makes the whole card clickable */
    .stButton>button {{
        width: 100%; height: 200px; background: transparent !important;
        color: transparent !important; border: none !important;
        position: absolute; top: 0; left: 0; z-index: 10; cursor: pointer;
    }}
    .stButton>button:hover {{ background: transparent !important; color: transparent !important; border: none !important; }}
    .stButton>button:active {{ background: transparent !important; border: none !important; }}

    /* Order Row Design */
    .order-row {{
        background: white; padding: 25px; border-radius: 20px; margin-bottom: 15px;
        border-left: 8px solid #3b82f6; display: flex; justify-content: space-between;
        align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }}
    
    .footer-box {{
        text-align: center; padding: 50px; color: #64748b; font-size: 14px;
        border-top: 1px solid #cbd5e1; margin-top: 100px;
    }}
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. DATA PROCESSING ENGINE
# ========================================================
@st.cache_data(ttl=2)
def fetch_complete_data():
    try:
        ts = int(time.time())
        base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={ts}&sheet="
        u = pd.read_csv(base_url + "Users").fillna('')
        s = pd.read_csv(base_url + "Settings").fillna('')
        o = pd.read_csv(base_url + "Orders").fillna('')
        f = pd.read_csv(base_url + "Feedback").fillna('')
        return u, s, o, f
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_db, settings_db, orders_db, feedback_db = fetch_complete_data()

def format_phone(p):
    s = str(p).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def generate_invoice_id(df):
    if df.empty or 'Invoice_ID' not in df.columns: return "0001"
    try:
        max_id = pd.to_numeric(df['Invoice_ID'], errors='coerce').max()
        return f"{int(max_id) + 1:04d}" if not pd.isna(max_id) else "0001"
    except: return "0001"

# ========================================================
# 4. SESSION & NAVIGATION CONTROL
# ========================================================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = {}
if 'current_screen' not in st.session_state: st.session_state.current_screen = "🏠 Dashboard"
if 'wizard_open' not in st.session_state: st.session_state.wizard_open = False
if 'wizard_step' not in st.session_state: st.session_state.wizard_step = 1
if 'order_data' not in st.session_state: st.session_state.order_data = {}
if 'admin_target_tab' not in st.session_state: st.session_state.admin_target_tab = 0

def navigate_to(screen, tab_idx=0):
    st.session_state.current_screen = screen
    st.session_state.admin_target_tab = tab_idx
    st.rerun()

# ========================================================
# 5. AUTHENTICATION MODULE
# ========================================================
if not st.session_state.auth:
    _, col_auth, _ = st.columns([1, 2, 1])
    with col_auth:
        st.markdown(f"<h1 style='text-align:center;'>{st.session_state.app_master['app_name']}</h1>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["🔐 Secure Login", "📝 New Registration"])
        
        with tab_login:
            login_ph = st.text_input("Mobile Number")
            login_pw = st.text_input("Access Password", type="password")
            if st.button("Unlock Dashboard 🚀", use_container_width=True):
                clean_ph = format_phone(login_ph)
                match = users_db[(users_db['Phone'].apply(format_phone) == clean_ph) & (users_db['Password'].astype(str) == login_pw)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("❌ Invalid Login Credentials.")
        
        with tab_reg:
            st.info("Please provide authentic information for factory verification.")
            reg_name = st.text_input("Full Registered Name")
            reg_ph = st.text_input("Active Mobile Number")
            reg_pw = st.text_input("Create Strong Password", type="password")
            if st.button("Submit Application ✨", use_container_width=True):
                if reg_name and reg_ph and reg_pw:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":reg_name, "phone":format_phone(reg_ph), "password":reg_pw})
                    st.success("✅ Application sent for approval! Contact Admin.")
    st.stop()

# ========================================================
# 6. SIDEBAR & IDENTITY
# ========================================================
user_info = st.session_state.user
u_name = user_info.get('Name', 'User')
u_phone = format_phone(user_info.get('Phone', ''))
is_admin_user = (u_phone == format_phone(ADMIN_PH))

with st.sidebar:
    st.markdown(f'''
        <div style="text-align:center; padding: 25px;">
            <img src="{user_info.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png')}" style="width:130px; height:130px; border-radius:50%; border:5px solid #3b82f6; object-fit: cover;">
            <h2 style="margin-top:15px; color:#1e293b;">{u_name}</h2>
            <span style="background:#dbeafe; color:#1e40af; padding:4px 12px; border-radius:20px; font-weight:600; font-size:12px;">{'ADMINISTRATOR' if is_admin_user else 'VALUED MEMBER'}</span>
        </div>
    ''', unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Home Dashboard", use_container_width=True): navigate_to("🏠 Dashboard")
    if st.button("🛍️ Book New Order", use_container_width=True, type="primary"):
        st.session_state.wizard_open = True
        st.session_state.wizard_step = 1
        st.rerun()
    if st.button("📜 Transaction History", use_container_width=True): navigate_to("📜 History")
    if st.button("👤 My Profile", use_container_width=True): navigate_to("👤 Profile")
    
    if is_admin_user:
        st.divider()
        st.markdown("🛠️ **MASTER CONTROL PANEL**")
        if st.button("🔐 Manager Dashboard", use_container_width=True): navigate_to("🔐 Admin")
    
    st.divider()
    if st.button("Logout 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()

# ========================================================
# 7. DASHBOARD MODULE (CLICKABLE CARDS)
# ========================================================
if st.session_state.current_screen == "🏠 Dashboard":
    st.header(f"Welcome back, {u_name}!")
    personal_orders = orders_db[orders_db['Phone'].apply(format_phone) == u_phone]
    
    # Calculation for Cards
    count_total = len(personal_orders)
    count_pending = len(personal_orders[personal_orders['Status'].str.contains('Pending|Process', case=False)])
    count_paid = len(personal_orders[personal_orders['Status'].str.contains('Paid|Complete', case=False)])
    count_members = len(users_db)

    # Clickable Cards Grid
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f'<div class="metric-card-wrapper"><div class="m-card c-total"><small>TOTAL BOOKINGS</small><h3>{count_total}</h3></div></div>', unsafe_allow_html=True)
        if st.button("", key="btn_card_total"): navigate_to("📜 History")
    
    with c2:
        st.markdown(f'<div class="metric-card-wrapper"><div class="m-card c-pending"><small>PENDING APPROVAL</small><h3>{count_pending}</h3></div></div>', unsafe_allow_html=True)
        if is_admin_user:
            if st.button("", key="btn_card_pending"): navigate_to("🔐 Admin", 0) # Tab 0 is Orders
        else:
            if st.button("", key="btn_card_pending_u"): navigate_to("📜 History")
            
    with c3:
        st.markdown(f'<div class="metric-card-wrapper"><div class="m-card c-complete"><small>PAID & COMPLETED</small><h3>{count_paid}</h3></div></div>', unsafe_allow_html=True)
        if is_admin_user:
            if st.button("", key="btn_card_paid"): navigate_to("🔐 Admin", 0)
        else:
            if st.button("", key="btn_card_paid_u"): navigate_to("📜 History")

    # This card only appears for Admin
    if is_admin_user:
        with c4:
            st.markdown(f'<div class="metric-card-wrapper"><div class="m-card c-active"><small>STORE MEMBERS</small><h3>{count_members}</h3></div></div>', unsafe_allow_html=True)
            if st.button("", key="btn_card_members"): navigate_to("🔐 Admin", 1) # Tab 1 is Users

    st.divider()
    st.subheader("🕒 Recent Transactions")
    if not personal_orders.empty:
        for _, row in personal_orders.tail(5).iloc[::-1].iterrows():
            st.markdown(f'''
                <div class="order-row">
                    <div><b>{row["Product"]}</b><br><small>{row["Timestamp"]}</small></div>
                    <div style="text-align:right;">
                        <span style="font-size:18px; font-weight:700;">Rs. {row["Bill"]}</span><br>
                        <span style="color:#2563eb; background:#eff6ff; padding:2px 8px; border-radius:10px; font-size:12px;">{row["Status"]}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("No recent activity found. Start by placing an order!")

# ========================================================
# 8. THE COMPLETE ORDER WIZARD (Phase 1-5)
# ========================================================
if st.session_state.wizard_open:
    @st.dialog("🛒 Professional Booking Gateway")
    def open_booking_wizard():
        step = st.session_state.wizard_step
        st.progress(step/5)
        st.write(f"Section {step} of 5")
        
        if step == 1:
            st.subheader("Select Category & Product")
            all_cats = settings_db['Category'].unique()
            s_cat = st.selectbox("Market Category", all_cats)
            available_prods = settings_db[settings_db['Category']==s_cat]['Product Name'].unique()
            s_prod = st.selectbox("Select Product", available_prods)
            if st.button("Continue to Details ➡️", use_container_width=True):
                st.session_state.order_data.update({"prod": s_prod})
                st.session_state.wizard_step = 2; st.rerun()
                
        elif step == 2:
            st.subheader("Specifications & Pricing")
            prod_info = settings_db[settings_db['Product Name'] == st.session_state.order_data['prod']].iloc[0]
            size_choice = st.radio("Choose Packing Size", ["20kg", "Gallon", "Quarter"], horizontal=True)
            quantity = st.number_input("Order Quantity", 1, 1000, 1)
            unit_price = float(prod_info.get(f"Price_{size_choice}", 0))
            total_bill = unit_price * quantity
            
            st.markdown(f"""
                <div style="background:#f8fafc; padding:20px; border-radius:15px; border:1px solid #e2e8f0;">
                    <p>Unit Price: Rs. {unit_price}</p>
                    <h2 style="color:#1e40af;">Total Bill: Rs. {total_bill}</h2>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Proceed to Payment ➡️", use_container_width=True):
                st.session_state.order_data.update({"size":size_choice, "qty":quantity, "bill":total_bill})
                st.session_state.wizard_step = 3; st.rerun()

        elif step == 3:
            st.subheader("Select Payment Gateway")
            pay_method = st.radio("Choose Method", ["JazzCash", "EasyPaisa", "Cash on Delivery (COD)"])
            st.warning("Note: Online payments require screenshot verification in the next step.")
            if st.button("Confirm Method ➡️", use_container_width=True):
                st.session_state.order_data['method'] = pay_method
                st.session_state.wizard_step = 4 if "COD" not in pay_method else 5
                st.rerun()

        elif step == 4:
            st.subheader("Digital Payment Verification")
            method = st.session_state.order_data['method']
            target_no = st.session_state.app_master['jc_no'] if "Jazz" in method else st.session_state.app_master['ep_no']
            qr_link = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={target_no}"
            
            st.markdown(f'''
                <div style="text-align:center; padding:20px; border:2px dashed #3b82f6; border-radius:20px;">
                    <img src="{qr_link}" width="180"><br>
                    <p style="margin-top:10px;">Send <b>Rs. {st.session_state.order_data['bill']}</b> to:</p>
                    <h1 style="color:#1e40af;">{target_no}</h1>
                    <small>Scan QR or transfer manually to verify.</small>
                </div>
            ''', unsafe_allow_html=True)
            
            proof_img = st.file_uploader("Upload Transaction Screenshot", type=['jpg', 'jpeg', 'png'])
            if proof_img and st.button("Submit Proof for Approval ✅", use_container_width=True):
                st.session_state.wizard_step = 5; st.rerun()

        elif step == 5:
            st.subheader("Final Review")
            order_summary = st.session_state.order_data
            st.write(f"**Item:** {order_summary['qty']}x {order_summary['prod']} ({order_summary['size']})")
            st.write(f"**Total Payable:** Rs. {order_summary['bill']}")
            st.write(f"**Payment Via:** {order_summary['method']}")
            
            if st.button("Place Final Order 🚀", type="primary", use_container_width=True):
                new_inv = generate_invoice_id(orders_db)
                requests.post(SCRIPT_URL, json={
                    "action": "order", 
                    "invoice_id": new_inv, 
                    "name": u_name, 
                    "phone": u_phone,
                    "product": f"{order_summary['qty']}x {order_summary['prod']} ({order_summary['size']})",
                    "bill": order_summary['bill'], 
                    "payment_method": order_summary['method']
                })
                st.session_state.wizard_open = False
                st.balloons()
                st.rerun()
    open_booking_wizard()

# ========================================================
# 9. ADMIN PANEL (FULL MASTER CONTROL)
# ========================================================
elif st.session_state.current_screen == "🔐 Admin" and is_admin_user:
    st.header("🛡️ Master Control Dashboard")
    
    # Selecting tab based on clickable card logic
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["🛒 Orders Management", "👥 User Database", "⚙️ Master App Settings"])
    
    with admin_tab1:
        st.subheader("All System Bookings")
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Paid", "Complete"])
        
        filtered_orders = orders_db
        if status_filter != "All":
            filtered_orders = orders_db[orders_db['Status'] == status_filter]
            
        for idx, row in filtered_orders.iloc[::-1].iterrows():
            with st.expander(f"Order #{row['Invoice_ID']} - {row['Name']} ({row['Status']})"):
                st.write(f"**Customer Phone:** {row['Phone']}")
                st.write(f"**Items:** {row['Product']}")
                st.write(f"**Amount:** Rs. {row['Bill']} | **Gateway:** {row['Payment_Method']}")
                st.write(f"**Timestamp:** {row['Timestamp']}")
                
                if row['Status'] != "Paid":
                    if st.button("Approve & Mark as Paid ✅", key=f"approve_btn_{idx}"):
                        requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                        st.success("Order status updated successfully!"); time.sleep(1); st.rerun()

    with admin_tab2:
        st.subheader("Member Directory")
        st.dataframe(users_db, use_container_width=True, hide_index=True)
        if st.button("Download User List (CSV)"):
            csv = users_db.to_csv(index=False).encode('utf-8')
            st.download_button("Click to Download", csv, "users.csv", "text/csv")

    with admin_tab3:
        st.subheader("🚀 System Global Settings")
        st.warning("Editing these will update the app for all users instantly.")
        
        m_name = st.text_input("Application Name", st.session_state.app_master['app_name'])
        m_jc = st.text_input("Master JazzCash No", st.session_state.app_master['jc_no'])
        m_ep = st.text_input("Master EasyPaisa No", st.session_state.app_master['ep_no'])
        m_email = st.text_input("Admin Support Email", st.session_state.app_master['admin_email'])
        m_footer = st.text_area("Footer Copyright Text", st.session_state.app_master['footer_text'])
        m_terms = st.text_area("Terms & Conditions", st.session_state.app_master['terms'])
        
        if st.button("Apply Global Changes 💾", type="primary"):
            st.session_state.app_master.update({
                "app_name": m_name, "jc_no": m_jc, "ep_no": m_ep,
                "admin_email": m_email, "footer_text": m_footer, "terms": m_terms
            })
            st.success("Global Settings Updated Successfully!"); time.sleep(1); st.rerun()

# ========================================================
# 10. HISTORY & PROFILE MODULES
# ========================================================
elif st.session_state.current_screen == "📜 History":
    st.header("📜 My Order History")
    hist_data = orders_db[orders_db['Phone'].apply(format_phone) == u_phone]
    if not hist_data.empty:
        st.dataframe(hist_data.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("You haven't placed any orders yet.")

elif st.session_state.current_screen == "👤 Profile":
    st.header("👤 Account Settings")
    prof_col1, prof_col2 = st.columns([1, 2])
    with prof_col1:
        st.image(user_info.get('Photo','https://cdn-icons-png.flaticon.com/512/149/149071.png'), width=200)
    with prof_col2:
        st.write(f"**Full Name:** {u_name}")
        st.write(f"**Phone Number:** {u_phone}")
        st.write(f"**Account Status:** Active")
        
        with st.expander("Update Security Password"):
            new_pass = st.text_input("New Password", type="password")
            if st.button("Change Password Now"):
                requests.post(SCRIPT_URL, json={"action":"update_password", "phone":u_phone, "password":new_pass})
                st.success("Password Updated!"); time.sleep(1); st.rerun()

# ========================================================
# 11. GLOBAL FOOTER
# ========================================================
st.markdown(f'''
    <div class="footer-box">
        {st.session_state.app_master["footer_text"]}<br>
        Support: {st.session_state.app_master["admin_email"]} | WhatsApp: {st.session_state.app_master["admin_no"]}
    </div>
''', unsafe_allow_html=True)
