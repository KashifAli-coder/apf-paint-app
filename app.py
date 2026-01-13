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
    try:
        t = int(time.time())
        base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
        u = pd.read_csv(base + "Users").fillna('')
        s = pd.read_csv(base + "Settings").fillna('')
        o = pd.read_csv(base + "Orders").fillna('')
        f = pd.read_csv(base + "Feedback").fillna('')
        return u, s, o, f
    except Exception as e:
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
# STEP 5: SIDEBAR (As per your original design)
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

# --- DASHBOARD (Same design as requested) ---
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
    st.subheader("🆕 Recent Activity")
    if not u_ords.empty:
        st.dataframe(u_ords.tail(3), use_container_width=True)

# --- NEW ORDER (Updated Logic for Paint Business) ---
elif menu == "🛍️ New Order":
    st.header("🛒 Create New Order (Paint Items)")
    
    if not settings_df.empty:
        # 1. Category and Product selection
        c1, c2 = st.columns(2)
        cat = c1.selectbox("Select Category", settings_df['Category'].unique())
        
        items_df = settings_df[settings_df['Category'] == cat]
        # Adding Sub-Category logic if available
        if 'Sub-Category' in items_df.columns:
            sub_cat = c2.selectbox("Sub-Category", items_df['Sub-Category'].unique())
            items_df = items_df[items_df['Sub-Category'] == sub_cat]

        prod_name = st.selectbox("Select Product", items_df['Product Name'].unique())
        prod_data = items_df[items_df['Product Name'] == prod_name].iloc[0]
        
        # 2. Price and Shade details
        c3, c4 = st.columns(2)
        price = float(prod_data['Price'])
        qty = c3.number_input(f"Quantity (Price: Rs. {price})", 1, 500, 1)
        shade = c4.text_input("Shade Code / Color Name", "Standard White")
        
        if st.button("Add to Cart 🛒", use_container_width=True):
            # Update/Confirm Logic: Check if product with same shade already in cart
            found = False
            for item in st.session_state.cart:
                if item['Product'] == prod_name and item['Shade'] == shade:
                    item['Qty'] += qty
                    item['Total'] = item['Qty'] * item['Price']
                    found = True
                    break
            if not found:
                st.session_state.cart.append({
                    "Product": prod_name, "Qty": qty, "Price": price, "Shade": shade, "Total": price * qty
                })
            st.success(f"Added {prod_name} ({shade}) to cart!")
            st.rerun()

        # 3. Cart Display and Management
        if st.session_state.cart:
            st.divider()
            st.subheader("📋 Your Cart Summary")
            final_bill = 0
            for i, itm in enumerate(st.session_state.cart):
                final_bill += itm['Total']
                col_item, col_del = st.columns([4, 1])
                col_item.write(f"**{itm['Product']}** ({itm['Shade']}) - {itm['Qty']} x {itm['Price']} = Rs. {itm['Total']}")
                if col_del.button("❌", key=f"del_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            
            st.markdown(f"### Total Bill: Rs. {final_bill}")
            
            # 4. Payment and Receipt
            pay_type = st.radio("Payment Method", ["COD", "JazzCash", "Bank Transfer"])
            receipt_b64 = ""
            if pay_type != "COD":
                st.info(f"Send Payment to: {JAZZCASH_NO}")
                file = st.file_uploader("Upload Payment Receipt (Screenshot)", type=['jpg','png','jpeg'])
                if file:
                    receipt_b64 = f"data:image/png;base64,{base64.b64encode(file.read()).decode()}"

            if st.button("Confirm & Place Order ✅", use_container_width=True, type="primary"):
                if pay_type != "COD" and not receipt_b64:
                    st.error("Please upload receipt first!")
                else:
                    inv = f"INV-{int(time.time())}"
                    items_str = ", ".join([f"{x['Qty']}x {x['Product']} ({x['Shade']})" for x in st.session_state.cart])
                    
                    requests.post(SCRIPT_URL, json={
                        "action":"order", "invoice_id":inv, "name":u_name, "phone":raw_ph,
                        "product":items_str, "bill":final_bill, "payment_method":pay_type, "receipt": receipt_b64
                    })
                    st.session_state.cart = []
                    st.success("Order Placed Successfully!")
                    time.sleep(1); set_nav("🏠 Dashboard")

# --- PROFILE, HISTORY, ADMIN (Same as previous versions) ---
elif menu == "👤 Profile":
    # (Profile logic wahi purani)
    st.markdown("### 👤 Profile Settings")
    st.markdown(f"""<div style="background-color: #f8f9fa; padding: 25px; border-radius: 15px; border-left: 6px solid #3b82f6;">
        <b>{u_name}</b><br>📱 {raw_ph}</div>""", unsafe_allow_html=True)
    img_file = st.file_uploader("Update Avatar", type=['png', 'jpg'])
    if img_file and st.button("Update Photo"):
        b64 = base64.b64encode(img_file.read()).decode()
        requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":raw_ph, "photo":f"data:image/png;base64,{b64}"})
        st.success("Updated!"); st.rerun()

elif menu == "📜 History":
    st.header("📜 Order History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    if not u_ords.empty:
        st.dataframe(u_ords, use_container_width=True)
    else: st.info("No orders found.")

elif menu == "💬 Feedback":
    st.header("💬 Feedback")
    f_msg = st.text_area("Message")
    if st.button("Submit"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":raw_ph, "message":f_msg})
        st.success("Sent!"); set_nav("🏠 Dashboard")

elif menu == "🔐 Admin":
    st.header("🛡️ Admin Panel")
    t1, t2 = st.tabs(["Orders", "Approvals"])
    with t1:
        st.dataframe(orders_df)
    with t2:
        p_u = users_df[users_df['Role'].str.lower() == 'pending']
        for idx, u in p_u.iterrows():
            st.write(f"{u['Name']} ({u['Phone']})")
            if st.button(f"Approve {idx}"):
                requests.post(SCRIPT_URL, json={"action":"approve_user", "phone":normalize_ph(u['Phone'])})
                st.rerun()
