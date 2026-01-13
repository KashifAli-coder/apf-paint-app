import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas

# ========================================================
# STEP 1: CONFIGURATION
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLQRD3dIUkQbNUi-Blo5WvBYqauD6NgMtYXDsC6-H1JLOgKShx8N5-ASHaNOR-QlOQ/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# --- UI STYLING ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; }
    .profile-img { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; display: block; margin: 0 auto; border: 3px solid #3b82f6; }
    .nav-header { text-align: center; padding: 10px; background: #f0f2f6; border-radius: 10px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ========================================================
# STEP 2: DATA FETCHING (MODULAR)
# ========================================================
@st.cache_data(ttl=0)
def load_all_data():
    t = int(time.time())
    base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
    try:
        u_df = pd.read_csv(base + "Users").fillna('')
        s_df = pd.read_csv(base + "Settings").fillna('')
        o_df = pd.read_csv(base + "Orders").fillna('')
        f_df = pd.read_csv(base + "Feedback").fillna('')
        return u_df, s_df, o_df, f_df
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    if s and not s.startswith('0'): return '0' + s
    return s

users_df, settings_df, orders_df, feedback_df = load_all_data()

# ========================================================
# STEP 3: PERSISTENT SESSION STATE
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = {}
    st.session_state.cart = []
    st.session_state.menu_choice = "🏠 Dashboard"

# ========================================================
# STEP 4: LOGIN & REGISTER MODULE
# ========================================================
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    with tab1:
        l_ph = st.text_input("Phone Number")
        l_pw = st.text_input("Password", type="password")
        if st.button("Login 🚀"):
            u_ph = normalize_ph(l_ph)
            match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == l_pw)]
            if not match.empty:
                user_row = match.iloc[0]
                if str(user_row['Role']).lower() == 'pending':
                    st.warning("⏳ Account Approval Pending...")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.to_dict()
                    st.rerun()
            else: st.error("Invalid Credentials")
    with tab2:
        r_name = st.text_input("Full Name")
        r_ph = st.text_input("Register Phone")
        r_pw = st.text_input("Create Password", type="password")
        if st.button("Register ✨"):
            requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_ph(r_ph), "password":r_pw})
            st.success("Registration Sent! Wait for Admin Approval.")
    st.stop()

# ========================================================
# STEP 5: CUSTOM SIDEBAR NAVIGATION (HTML/CSS LOGIC)
# ========================================================
u_data = st.session_state.user_data
u_name = u_data.get('Name', 'User')
raw_ph = normalize_ph(u_data.get('Phone', ''))
u_photo = u_data.get('Photo', '')

# Profile Display
sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
st.sidebar.markdown(f'<img src="{sidebar_img}" class="profile-img">', unsafe_allow_html=True)
st.sidebar.markdown(f"<div class='nav-header'><b>👤 {u_name}</b></div>", unsafe_allow_html=True)

# Navigation Buttons (Modular Control)
if st.sidebar.button("🏠 Dashboard"): st.session_state.menu_choice = "🏠 Dashboard"; st.rerun()
if st.sidebar.button("👤 Profile"): st.session_state.menu_choice = "👤 Profile"; st.rerun()
if st.sidebar.button("🛍️ New Order"): st.session_state.menu_choice = "🛍️ New Order"; st.rerun()
if st.sidebar.button("📜 History"): st.session_state.menu_choice = "📜 History"; st.rerun()
if st.sidebar.button("💬 Feedback"): st.session_state.menu_choice = "💬 Feedback"; st.rerun()

if raw_ph == normalize_ph(JAZZCASH_NO): # Admin Check
    if st.sidebar.button("🔐 Admin"): st.session_state.menu_choice = "🔐 Admin"; st.rerun()

if st.sidebar.button("Logout 🚪"): 
    st.session_state.clear(); st.rerun()

# ========================================================
# MODULE: DASHBOARD
# ========================================================
if st.session_state.menu_choice == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    my_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    
    pending = my_ords[my_ords['Status'].str.contains("Order|Pending", case=False, na=False)]
    if not pending.empty:
        st.warning(f"⚠️ Aapke {len(pending)} orders abhi approve hona baqi hain.")

    c1, c2 = st.columns(2)
    c1.metric("Total Orders", len(my_ords))
    c2.metric("Total Bill", f"Rs. {my_ords['Bill'].sum()}")
    st.subheader("Recent Activity")
    st.dataframe(my_ords.tail(5), use_container_width=True)

# ========================================================
# MODULE: PROFILE (STEP 6)
# ========================================================
elif st.session_state.menu_choice == "👤 Profile":
    st.title("👤 My Profile")
    st.write(f"**Name:** {u_name}")
    st.write(f"**Phone:** {raw_ph}")
    
    with st.expander("Update Profile Photo"):
        img_file = st.file_uploader("Choose Image", type=['png', 'jpg', 'jpeg'])
        if img_file and st.button("Save Photo ✅"):
            b64 = base64.b64encode(img_file.read()).decode()
            photo_data = f"data:image/png;base64,{b64}"
            requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":raw_ph, "photo":photo_data})
            st.session_state.user_data['Photo'] = photo_data
            st.success("Photo Updated!"); time.sleep(1); st.rerun()

# ========================================================
# MODULE: ORDERING SYSTEM (STEP 7-13)
# ========================================================
elif st.session_state.menu_choice == "🛍️ New Order":
    st.title("🛍️ New Order")
    
    # Selection Module
    cat = st.selectbox("Select Category", settings_df['Category'].unique())
    items = settings_df[settings_df['Category'] == cat]
    prod = st.selectbox("Select Product", items['Product Name'])
    price = float(items[items['Product Name'] == prod]['Price'].values[0])
    qty = st.number_input("Quantity", 1, 100, 1)
    
    if st.button("Add to Cart 🛒"):
        st.session_state.cart.append({"Product": prod, "Price": price, "Qty": qty, "Total": price*qty})
        st.rerun()

    # Cart & Checkout Module
    if st.session_state.cart:
        st.divider()
        total = 0
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{item['Qty']}x {item['Product']} - Rs. {item['Total']}")
            total += item['Total']
        
        st.info(f"**Total Payable: Rs. {total}**")
        pay_method = st.radio("Payment", ["COD", "JazzCash", "EasyPaisa"])
        
        if st.button("Confirm & Place Order ✅"):
            inv_id = f"INV-{int(time.time())}"
            all_prods = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
            requests.post(SCRIPT_URL, json={
                "action":"order", "invoice_id":inv_id, "name":u_name, 
                "phone":raw_ph, "product":all_prods, "bill":total, "payment_method":pay_method
            })
            st.session_state.cart = []
            st.success("Order Placed Successfully!")
            time.sleep(2)
            st.session_state.menu_choice = "🏠 Dashboard"
            st.rerun()

# ========================================================
# MODULE: HISTORY (STEP 14)
# ========================================================
elif st.session_state.menu_choice == "📜 History":
    st.title("📜 Order History")
    my_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    st.dataframe(my_ords[['Date', 'Invoice_ID', 'Product', 'Bill', 'Status']], use_container_width=True)

# ========================================================
# MODULE: FEEDBACK (STEP 15)
# ========================================================
elif st.session_state.menu_choice == "💬 Feedback":
    st.title("💬 Feedback")
    msg = st.text_area("Your Message", height=150)
    if st.button("Submit Feedback 📩"):
        if msg:
            requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":raw_ph, "message":msg})
            st.balloons()
            st.success("Thank you! Redirecting...")
            time.sleep(2)
            st.session_state.menu_choice = "🏠 Dashboard"
            st.rerun()

# ========================================================
# MODULE: ADMIN (STEP 16)
# ========================================================
elif st.session_state.menu_choice == "🔐 Admin":
    st.title("🔐 Admin Panel")
    t1, t2, t3 = st.tabs(["Orders", "Users", "Feedback"])
    with t1: st.dataframe(orders_df)
    with t2: st.dataframe(users_df)
    with t3: st.dataframe(feedback_df)
