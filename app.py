import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas

# ========================================================
# STEP 1: CONFIGURATION (Module 1)
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLQRD3dIUkQbNUi-Blo5WvBYqauD6NgMtYXDsC6-H1JLOgKShx8N5-ASHaNOR-QlOQ/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# ========================================================
# STEP 2: DATA LOADING (Module 2)
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
# STEP 3-5: NAVIGATION & SESSION (Module 3)
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_data': {}, 'cart': [], 'menu_choice': "🏠 Dashboard"})

def set_nav(target):
    st.session_state.menu_choice = target
    st.rerun()

# --- Login Check ---
if not st.session_state.logged_in:
    # (Step 4: Login/Register Logic)
    l_ph = st.text_input("Phone")
    l_pw = st.text_input("Password", type="password")
    if st.button("Login"):
        u_ph = normalize_ph(l_ph)
        match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == l_pw)]
        if not match.empty:
            st.session_state.logged_in = True
            st.session_state.user_data = match.iloc[0].to_dict()
            st.rerun()
    st.stop()

# --- Sidebar Buttons (HTML Logic) ---
st.sidebar.title("Navigation")
if st.sidebar.button("🏠 Dashboard"): set_nav("🏠 Dashboard")
if st.sidebar.button("🛍️ New Order"): set_nav("🛍️ New Order")
if st.sidebar.button("📜 History"): set_nav("📜 History")
if st.sidebar.button("💬 Feedback"): set_nav("💬 Feedback")
if normalize_ph(st.session_state.user_data['Phone']) == normalize_ph(JAZZCASH_NO):
    if st.sidebar.button("🔐 Admin"): set_nav("🔐 Admin")

menu = st.session_state.menu_choice
u_name = st.session_state.user_data['Name']
raw_ph = normalize_ph(st.session_state.user_data['Phone'])

# ========================================================
# STEP 7: PRODUCT SELECTION (Module 7)
# ========================================================
if menu == "🛍️ New Order":
    st.header("Step 7: Select Product")
    scat = st.selectbox("Category", settings_df['Category'].unique())
    items = settings_df[settings_df['Category'] == scat]
    sprod = st.selectbox("Product", items['Product Name'])
    prc = float(items[items['Product Name'] == sprod]['Price'].values[0])
    qty = st.number_input("Quantity", 1, 100, 1)
    
    if st.button("Add to Cart 🛒"):
        st.session_state.cart.append({"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty})
        st.rerun()

# ========================================================
# STEP 8: CART REVIEW (Module 8)
# ========================================================
    st.divider()
    st.header("Step 8: Cart Review")
    if not st.session_state.cart:
        st.write("Cart is empty.")
    else:
        for i, itm in enumerate(st.session_state.cart):
            st.write(f"{itm['Qty']}x {itm['Product']} = Rs. {itm['Total']}")
            if st.button(f"Remove {i}", key=f"del_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()

# ========================================================
# STEP 9: BILL CALCULATION (Module 9)
# ========================================================
    st.divider()
    st.header("Step 9: Bill Total")
    final_bill = sum(x['Total'] for x in st.session_state.cart)
    st.subheader(f"Total: Rs. {final_bill}")

# ========================================================
# STEP 10: PAYMENT METHOD (Module 10)
# ========================================================
    st.divider()
    st.header("Step 10: Select Payment")
    pay_type = st.radio("Method", ["COD", "JazzCash", "EasyPaisa"])

# ========================================================
# STEP 11: QR DISPLAY (Module 11)
# ========================================================
    st.divider()
    st.header("Step 11: QR Payment (If Applicable)")
    if pay_type != "COD":
        st.write(f"Send to: {JAZZCASH_NO}")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={final_bill}")

# ========================================================
# STEP 12: ORDER CONFIRMATION (Module 12)
# ========================================================
    st.divider()
    st.header("Step 12: Final Confirmation")
    if st.button("Confirm & Order Now ✅"):
        if st.session_state.cart:
            inv = f"INV-{int(time.time())}"
            prods = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
            requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv, "name":u_name, "phone":raw_ph, "product":prods, "bill":final_bill, "payment_method":pay_type})
            st.session_state.cart = []
            st.success("Order Placed!")
            time.sleep(1)
            set_nav("🏠 Dashboard")
        else:
            st.error("Cart is empty!")

# ========================================================
# STEP 13: WHATSAPP LINK (Module 13)
# ========================================================
    st.divider()
    st.header("Step 13: Support")
    st.markdown(f"[Message Support](https://wa.me/923005508112?text=OrderDetails)")

# ========================================================
# STEP 16: ADMIN PANEL (FULL & COMPLETE)
# ========================================================
elif menu == "🔐 Admin":
    st.header("Step 16: Admin Control Panel")
    ad_tabs = st.tabs(["Manage Orders", "User Approvals", "Feedback Logs"])
    
    with ad_tabs[0]: # Orders Module
        st.subheader("All Orders")
        for idx, row in orders_df.iterrows():
            st.write(f"ID: {row['Invoice_ID']} | {row['Name']} | {row['Status']}")
            if st.button(f"Mark Paid {idx}", key=f"paid_{idx}"):
                requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                st.rerun()

    with ad_tabs[1]: # Approval Module
        st.subheader("Pending Users")
        pending_u = users_df[users_df['Role'].str.lower() == 'pending']
        for idx, u in pending_u.iterrows():
            st.write(f"{u['Name']} ({u['Phone']})")
            if st.button(f"Approve {idx}", key=f"app_{idx}"):
                requests.post(SCRIPT_URL, json={"action":"approve_user", "phone":normalize_ph(u['Phone'])})
                st.rerun()

    with ad_tabs[2]: # Feedback Module
        st.dataframe(feedback_df)

# (Dashboard, History, Feedback modules wahi rahenge...)
