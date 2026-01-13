import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# STEP 1: CONFIGURATION
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
# Aapka SCRIPT_URL
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzuMMPIoME0v7ZUAu_EzWK1oDjqB_YaRtejtO3_a7clBCl3Yjr69_sZQA6JykLo5Kuj/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# ========================================================
# STEP 2: DATA LOADING
# ========================================================
@st.cache_data(ttl=0)
def load_all_data():
    try:
        t = int(time.time())
        base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
        u = pd.read_csv(base + "Users").fillna('')
        s = pd.read_csv(base + "Settings").fillna('')
        o = pd.read_csv(base + "Orders").fillna('')
        f = pd.read_csv(base + "Feedback").fillna('')
        return u, s, o, f
    except Exception as e:
        st.error(f"Data loading error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_df, settings_df, orders_df, feedback_df = load_all_data()

def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    if s and not s.startswith('0'): return '0' + s
    return s

# ========================================================
# STEP 3: SESSION STATE
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_data': {}, 'cart': [], 'menu_choice': "🏠 Dashboard"})

def set_nav(target):
    st.session_state.menu_choice = target
    st.rerun()

# ========================================================
# STEP 4: LOGIN & REGISTER
# ========================================================
if not st.session_state.logged_in:
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        l_ph = st.text_input("Phone", key="login_ph")
        l_pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login 🚀", key="login_btn"):
            u_ph = normalize_ph(l_ph)
            match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == l_pw)]
            if not match.empty:
                user_row = match.iloc[0]
                if str(user_row['Role']).lower() == 'pending': 
                    st.warning("Awaiting Approval")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.to_dict()
                    st.rerun()
            else: 
                st.error("Login Failed")
    with t2:
        r_name = st.text_input("Name", key="reg_name")
        r_ph = st.text_input("Phone Number", key="reg_ph")
        r_pw = st.text_input("Password", type="password", key="reg_pw")
        if st.button("Register ✨", key="reg_btn"):
            requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_ph(r_ph), "password":r_pw})
            st.success("Registered! Wait for admin.")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR
# ========================================================
u_data = st.session_state.get('user_data', {})
u_name = u_data.get('Name', 'User')
raw_ph = normalize_ph(u_data.get('Phone', ''))
u_photo = u_data.get('Photo', '')

sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan' and u_photo != '') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"

st.sidebar.markdown(f'<div style="text-align:center"><img src="{sidebar_img}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; border:2px solid #3b82f6;"></div>', unsafe_allow_html=True)
st.sidebar.header(f"Welcome, {u_name}")

if st.sidebar.button("🏠 Dashboard"): set_nav("🏠 Dashboard")
if st.sidebar.button("👤 Profile"): set_nav("👤 Profile")
if st.sidebar.button("🛍️ New Order"): set_nav("🛍️ New Order")
if st.sidebar.button("📜 History"): set_nav("📜 History")
if st.sidebar.button("💬 Feedback"): set_nav("💬 Feedback")

if raw_ph == normalize_ph(JAZZCASH_NO):
    if st.sidebar.button("🔐 Admin"): set_nav("🔐 Admin")

if st.sidebar.button("Logout 🚪"): 
    st.session_state.clear()
    st.rerun()

menu = st.session_state.menu_choice

# ========================================================
# STEP 6: MODULES (DASHBOARD, PROFILE, ETC)
# ========================================================

# --- DASHBOARD ---
if menu == "🏠 Dashboard":
    st.markdown(f"## 🏠 Welcome back, {u_name}!")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    total_spent = u_ords['Bill'].sum() if not u_ords.empty else 0
    total_orders = len(u_ords)
    
    st.markdown("""
        <style>
        .card-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
        .stat-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; flex: 1; border-bottom: 4px solid #3b82f6; }
        .stat-card h3 { margin: 0; color: #6b7280; font-size: 14px; text-transform: uppercase; }
        .stat-card p { margin: 10px 0 0 0; color: #111827; font-size: 24px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="card-container">
            <div class="stat-card"><h3>📦 Total Orders</h3><p>{total_orders}</p></div>
            <div class="stat-card"><h3>💰 Total Spent</h3><p>Rs. {total_spent}</p></div>
            <div class="stat-card" style="border-bottom: 4px solid #10b981;"><h3>🛡️ Account</h3><p>Verified</p></div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    col_act, col_info = st.columns([2, 1])
    with col_act:
        st.subheader("🆕 Recent Activity")
        if not u_ords.empty:
            for _, row in u_ords.tail(3).iterrows():
                st.markdown(f"""
                    <div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #e5e7eb;">
                        <strong>Invoice: {row['Invoice_ID']}</strong> | Rs. {row['Bill']}<br>
                        <small>Status: {row['Status']}</small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activity found.")
    with col_info:
        st.subheader("⚡ Quick Links")
        if st.button("🛍️ New Order Now", use_container_width=True): set_nav("🛍️ New Order")

# --- PROFILE ---
elif menu == "👤 Profile":
    st.markdown("### 👤 Profile Settings")
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 25px; border-radius: 15px; border-left: 6px solid #3b82f6; margin-bottom: 25px;">
        <div style="display: flex; align-items: center;">
            <img src="{sidebar_img}" style="width: 90px; height: 90px; border-radius: 50%; object-fit: cover; margin-right: 25px;">
            <div><h2 style="margin: 0;">{u_name}</h2><p style="margin: 5px 0;">📱 {raw_ph}</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        img_file = st.file_uploader("Update Avatar", type=['png', 'jpg', 'jpeg'])
        if img_file and st.button("Update Photo ✨"):
            b64 = base64.b64encode(img_file.read()).decode()
            photo_data = f"data:image/png;base64,{b64}"
            requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":raw_ph, "photo":photo_data})
            st.session_state.user_data['Photo'] = photo_data
            st.success("Updated!"); time.sleep(1); st.rerun()
    with c2:
        new_pw = st.text_input("New Password", type="password")
        if st.button("Change Password 🛡️"):
            requests.post(SCRIPT_URL, json={"action":"update_password", "phone":raw_ph, "password":new_pw})
            st.success("Password Updated!")

# --- NEW ORDER ---
elif menu == "🛍️ New Order":
    st.header("🛒 Create New Order")
    if settings_df.empty:
        st.error("Settings data not found. Contact Admin.")
    else:
        scat = st.selectbox("Category", settings_df['Category'].unique())
        items = settings_df[settings_df['Category'] == scat]
        sprod = st.selectbox("Product", items['Product Name'])
        prc = float(items[items['Product Name'] == sprod]['Price'].values[0])
        qty = st.number_input("Quantity", 1, 100, 1)
        
        if st.button("Add to Cart 🛒"):
            st.session_state.cart.append({"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty})
            st.success("Added!")
            st.rerun()

        if st.session_state.cart:
            st.divider()
            st.subheader("🛒 Your Cart")
            for i, itm in enumerate(st.session_state.cart):
                col_item, col_del = st.columns([4, 1])
                col_item.write(f"{itm['Qty']}x {itm['Product']} = Rs. {itm['Total']}")
                if col_del.button("❌", key=f"del_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            
            final_bill = sum(x['Total'] for x in st.session_state.cart)
            st.subheader(f"Total: Rs. {final_bill}")
            pay_type = st.radio("Method", ["COD", "JazzCash", "EasyPaisa"])
            
            if pay_type != "COD":
                st.info(f"Send to: {JAZZCASH_NO}")
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={final_bill}")

            if st.button("Confirm Order ✅"):
                inv = f"INV-{int(time.time())}"
                prods = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
                requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv, "name":u_name, "phone":raw_ph, "product":prods, "bill":final_bill, "payment_method":pay_type})
                st.session_state.cart = []
                st.success("Order Placed!"); time.sleep(1); set_nav("🏠 Dashboard")

# --- HISTORY MODULE (Attractive Card Style) ---
elif menu == "📜 History":
    st.header("📜 Order History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    
    if not u_ords.empty:
        # Sort by latest first
        for _, row in u_ords.iloc[::-1].iterrows():
            status = str(row['Status'])
            # Color logic
            bg_color = "#dcfce7" if "Paid" in status else "#fef3c7"
            text_color = "#166534" if "Paid" in status else "#92400e"
            icon = "✅" if "Paid" in status else "⏳"

            st.markdown(f"""
                <div style="background: white; padding: 20px; border-radius: 15px; margin-bottom: 15 dashed #e5e7eb; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 6px solid {'#10b981' if 'Paid' in status else '#f59e0b'};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 14px; font-weight: bold; color: #6b7280;">#{row['Invoice_ID']}</span>
                        <span style="background: {bg_color}; color: {text_color}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                            {icon} {status}
                        </span>
                    </div>
                    <div style="margin-top: 10px;">
                        <h4 style="margin: 0; color: #111827;">{row['Product']}</h4>
                        <p style="margin: 5px 0; font-size: 18px; font-weight: bold; color: #3b82f6;">Rs. {row['Bill']}</p>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px; border-top: 1px solid #f3f4f6; padding-top: 10px;">
                        <span style="font-size: 12px; color: #9ca3af;">💳 {row['Payment_Method']}</span>
                        <span style="font-size: 12px; color: #9ca3af;">📅 {str(row['Timestamp'])[:16]}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Abhi tak koi order history mojud nahi hai.")

# --- FEEDBACK ---
elif menu == "💬 Feedback":
    st.header("💬 Feedback")
    f_msg = st.text_area("Message")
    if st.button("Submit Feedback"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":raw_ph, "message":f_msg})
        st.success("Sent!"); time.sleep(1); set_nav("🏠 Dashboard")

# --- ADMIN PANEL (Modern Control Style) ---
elif menu == "🔐 Admin":
    st.header("🛡️ Administrator Control")
    t1, t2, t3 = st.tabs(["📦 Orders Management", "👥 User Approvals", "💬 Feedback Logs"])
    
    with t1:
        if not orders_df.empty:
            for idx, row in orders_df.iterrows():
                with st.container():
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"""
                            <div style="background: #f9fafb; padding: 15px; border-radius: 10px; border: 1px solid #e5e7eb;">
                                <b>Customer:</b> {row['Name']} ({row['Phone']})<br>
                                <b>Items:</b> {row['Product']}<br>
                                <b>Total:</b> Rs. {row['Bill']} | <b>Method:</b> {row['Payment_Method']}<br>
                                <b>Status:</b> <span style="color: {'green' if 'Paid' in str(row['Status']) else 'red'}">{row['Status']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    with col_btn:
                        if "Paid" not in str(row['Status']):
                            if st.button(f"Mark Paid", key=f"pay_{idx}", use_container_width=True):
                                requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                                st.success("Updated!")
                                time.sleep(1)
                                st.rerun()
                st.write("") # Spacer
        else:
            st.write("No orders to manage.")

    with t2:
        p_u = users_df[users_df['Role'].str.lower() == 'pending']
        if not p_u.empty:
            for idx, u in p_u.iterrows():
                c_u1, c_u2 = st.columns([3, 1])
                c_u1.info(f"**Name:** {u['Name']} \n\n **Phone:** {u['Phone']}")
                if c_u2.button(f"Approve ✅", key=f"app_{idx}", use_container_width=True):
                    requests.post(SCRIPT_URL, json={"action":"approve_user", "phone":normalize_ph(u['Phone'])})
                    st.success("User Approved!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.success("No pending approvals! All caught up.")

    with t3:
        st.subheader("Customer Reviews")
        if not feedback_df.empty:
            for _, f in feedback_df.iloc[::-1].iterrows():
                st.markdown(f"""
                    <div style="background: #ffffff; padding: 15px; border-radius: 10px; border-left: 4px solid #8b5cf6; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-weight: bold; color: #4b5563;">{f['Name']} <span style="font-weight: normal; font-size: 12px;">({f['Phone']})</span></div>
                        <div style="margin-top: 5px; color: #1f2937;">"{f['Message']}"</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No feedback yet.")
