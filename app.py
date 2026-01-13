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

# ========================================================
# STEP 6: DASHBOARD & PROFILE (REPLACEMENT CODE)
# ========================================================

# --- DASHBOARD MODULE ---
if menu == "🏠 Dashboard":
    st.header("🏠 Dashboard")
    # Dashboard stats aur orders dikhane ke liye logic
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Orders", len(u_ords))
    c2.metric("Total Spent", f"Rs. {u_ords['Bill'].sum()}")
    c3.metric("Status", "Active")

    st.subheader("Recent Activity")
    st.dataframe(u_ords.tail(5), use_container_width=True)

# --- PROFILE MODULE (Social Media Style) ---
elif menu == "👤 Profile":
    st.markdown("### 👤 User Profile Settings")
    
    # Visual Social Media Card
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 25px; border-radius: 15px; border-left: 6px solid #3b82f6; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <div style="display: flex; align-items: center;">
            <img src="{sidebar_img}" style="width: 90px; height: 90px; border-radius: 50%; object-fit: cover; margin-right: 25px; border: 3px solid #fff; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div>
                <h2 style="margin: 0; color: #111827; font-family: sans-serif;">{u_name}</h2>
                <p style="margin: 5px 0; color: #4b5563; font-size: 16px;">📱 {raw_ph}</p>
                <div style="display: inline-block; background: #dcfce7; color: #166534; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">Verified Profile</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🖼️ Profile Picture")
        st.write("Update your avatar")
        img_file = st.file_uploader("Choose image...", type=['png', 'jpg', 'jpeg'], key="p_img_up")
        if img_file:
            if st.button("Update Photo ✨", key="up_photo_btn"):
                b64 = base64.b64encode(img_file.read()).decode()
                photo_data = f"data:image/png;base64,{b64}"
                # Google Sheet API Call
                requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":raw_ph, "photo":photo_data})
                st.session_state.user_data['Photo'] = photo_data
                st.success("Photo Updated!")
                time.sleep(1)
                st.rerun()

    with col2:
        st.subheader("🔐 Password & Security")
        st.write("Keep your account safe")
        new_pw = st.text_input("New Password", type="password", key="n_pass")
        conf_pw = st.text_input("Confirm New Password", type="password", key="c_pass")
        
        if st.button("Change Password 🛡️", key="up_pass_btn"):
            if new_pw and new_pw == conf_pw:
                # Google Sheet API Call
                requests.post(SCRIPT_URL, json={"action":"update_password", "phone":raw_ph, "password":new_pw})
                st.success("Password Updated Successfully!")
            elif new_pw != conf_pw:
                st.error("Passwords do not match!")
            else:
                st.warning("Please enter a password.")

    st.divider()
    st.info("⚠️ **Note:** For security reasons, your Name and Phone Number are locked. Please contact the administrator if you need to update them.")
    

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
