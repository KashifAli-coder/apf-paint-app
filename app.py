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
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzuMMPIoME0v7ZUAu_EzWK1oDjqB_YaRtejtO3_a7clBCl3Yjr69_sZQA6JykLo5Kuj/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# ========================================================
# STEP 2: DATA LOADING
# ========================================================
@st.cache_data(ttl=0)
def load_all_data():
    t = int(time.time())
    base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
    u = pd.read_csv(base + "Users").fillna('')
    s = pd.read_csv(base + "Settings").fillna('')
    o = pd.read_csv(base + "Orders").fillna('')
    f = pd.read_csv(base + "Feedback").fillna('')
    return u, s, o, f

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
# STEP 4: LOGIN & REGISTER (Fixed Duplicate ID)
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
                if str(user_row['Role']).lower() == 'pending': st.warning("Awaiting Approval")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.to_dict()
                    st.rerun()
            else: st.error("Login Failed")
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

sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
st.sidebar.markdown(f'<div style="text-align:center"><img src="{sidebar_img}" style="width:100px;border-radius:50%"></div>', unsafe_allow_html=True)
st.sidebar.header(f"Welcome, {u_name}")

if st.sidebar.button("🏠 Dashboard"): set_nav("🏠 Dashboard")
if st.sidebar.button("👤 Profile"): set_nav("👤 Profile") # Profile Button
if st.sidebar.button("🛍️ New Order"): set_nav("🛍️ New Order")
if st.sidebar.button("📜 History"): set_nav("📜 History")
if st.sidebar.button("💬 Feedback"): set_nav("💬 Feedback")

if raw_ph and raw_ph == normalize_ph(JAZZCASH_NO):
    if st.sidebar.button("🔐 Admin"): set_nav("🔐 Admin")

if st.sidebar.button("Logout 🚪"): 
    st.session_state.clear()
    st.rerun()

menu = st.session_state.menu_choice

# --- DASHBOARD MODULE (Modern Social Style) ---
if menu == "🏠 Dashboard":
    st.markdown(f"## 🏠 Welcome back, {u_name}!")
    
    # User Stats Summary Cards
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    total_spent = u_ords['Bill'].sum() if not u_ords.empty else 0
    total_orders = len(u_ords)
    
    # CSS for Social Media Style Cards
    st.markdown("""
        <style>
        .card-container {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 20px;
        }
        .stat-card {
            background-color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            flex: 1;
            border-bottom: 4px solid #3b82f6;
        }
        .stat-card h3 { margin: 0; color: #6b7280; font-size: 14px; text-transform: uppercase; }
        .stat-card p { margin: 10px 0 0 0; color: #111827; font-size: 24px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    # Displaying Stats in Columns (Social Cards)
    st.markdown(f"""
        <div class="card-container">
            <div class="stat-card">
                <h3>📦 Total Orders</h3>
                <p>{total_orders}</p>
            </div>
            <div class="stat-card">
                <h3>💰 Total Spent</h3>
                <p>Rs. {total_spent}</p>
            </div>
            <div class="stat-card" style="border-bottom: 4px solid #10b981;">
                <h3>🛡️ Account</h3>
                <p>Verified</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Layout for Recent Activity and Quick Actions
    col_act, col_info = st.columns([2, 1])

    with col_act:
        st.subheader("🆕 Recent Activity")
        if not u_ords.empty:
            # Custom display for recent orders
            for _, row in u_ords.tail(3).iterrows():
                with st.container():
                    st.markdown(f"""
                        <div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #e5e7eb;">
                            <div style="display: flex; justify-content: space-between;">
                                <strong>Invoice: {row['Invoice_ID']}</strong>
                                <span style="color: #3b82f6; font-weight: bold;">Rs. {row['Bill']}</span>
                            </div>
                            <div style="font-size: 13px; color: #6b7280; margin-top: 5px;">
                                Items: {row['Product']}<br>
                                Status: <span style="color: {'#10b981' if 'Paid' in str(row['Status']) else '#f59e0b'}">● {row['Status']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Abhi tak koi order nahi kiya gaya.")

    with col_info:
        st.subheader("⚡ Quick Links")
        st.button("🛍️ New Order", on_click=lambda: set_nav("🛍️ New Order"), use_container_width=True)
        st.button("📜 View History", on_click=lambda: set_nav("📜 History"), use_container_width=True)
        
        st.markdown("""
            <div style="background: #eff6ff; padding: 15px; border-radius: 10px; margin-top: 15px;">
                <p style="margin:0; font-size: 13px; color: #1e40af;">
                    <b>Offer:</b> Get 10% off on your next order using EasyPaisa!
                </p>
            </div>
        """, unsafe_allow_html=True)

# --- PROFILE MODULE --- (Same as before but integrated)
elif menu == "👤 Profile":
    # (Aapka pehle wala Social Profile code yahan rahega)
# ========================================================
# MODULE: NEW ORDER (Steps 7-13)
# ========================================================
elif menu == "🛍️ New Order":
    st.header("Step 7: Select Product")
    scat = st.selectbox("Category", settings_df['Category'].unique())
    items = settings_df[settings_df['Category'] == scat]
    sprod = st.selectbox("Product", items['Product Name'])
    prc = float(items[items['Product Name'] == sprod]['Price'].values[0])
    qty = st.number_input("Quantity", 1, 100, 1)
    
    if st.button("Add to Cart 🛒"):
        st.session_state.cart.append({"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty})
        st.rerun()

    st.divider()
    st.header("Step 8: Cart Review")
    if not st.session_state.cart:
        st.write("Cart is empty.")
    else:
        for i, itm in enumerate(st.session_state.cart):
            st.write(f"{itm['Qty']}x {itm['Product']} = Rs. {itm['Total']}")
            if st.button(f"Remove Item {i}", key=f"del_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()

        st.divider()
        st.header("Step 9: Bill Total")
        final_bill = sum(x['Total'] for x in st.session_state.cart)
        st.subheader(f"Total: Rs. {final_bill}")

        st.divider()
        st.header("Step 10: Select Payment")
        pay_type = st.radio("Method", ["COD", "JazzCash", "EasyPaisa"])

        st.divider()
        st.header("Step 11: QR Payment")
        if pay_type != "COD":
            st.write(f"Send to: {JAZZCASH_NO}")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={final_bill}")

        st.divider()
        st.header("Step 12: Final Confirmation")
        if st.button("Confirm & Order Now ✅"):
            inv = f"INV-{int(time.time())}"
            prods = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
            requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv, "name":u_name, "phone":raw_ph, "product":prods, "bill":final_bill, "payment_method":pay_type})
            st.session_state.cart = []
            st.success("Order Placed!")
            time.sleep(1)
            set_nav("🏠 Dashboard")

        st.divider()
        st.header("Step 13: Support")
        st.markdown(f"[Message Support](https://wa.me/923005508112?text=OrderDetails)")

# ========================================================
# STEP 14: HISTORY
# ========================================================
elif menu == "📜 History":
    st.header("📜 History")
    st.dataframe(orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph], use_container_width=True)

# ========================================================
# STEP 15: FEEDBACK
# ========================================================
elif menu == "💬 Feedback":
    st.header("💬 Feedback")
    f_msg = st.text_area("Message")
    if st.button("Submit Feedback"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":raw_ph, "message":f_msg})
        st.success("Sent!"); time.sleep(1); set_nav("🏠 Dashboard")

# ========================================================
# STEP 16: ADMIN PANEL
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Panel")
    ad_tabs = st.tabs(["Orders", "Approvals", "Feedback Logs"])
    with ad_tabs[0]:
        for idx, row in orders_df.iterrows():
            st.write(f"ID: {row['Invoice_ID']} | {row['Status']}")
            if st.button(f"Mark Paid {idx}", key=f"p_{idx}"):
                requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                st.rerun()
    with ad_tabs[1]:
        p_u = users_df[users_df['Role'].str.lower() == 'pending']
        for idx, u in p_u.iterrows():
            st.write(u['Name'])
            if st.button(f"Approve {idx}", key=f"a_{idx}"):
                requests.post(SCRIPT_URL, json={"action":"approve_user", "phone":normalize_ph(u['Phone'])})
                st.rerun()
    with ad_tabs[2]:
        st.dataframe(feedback_df)
