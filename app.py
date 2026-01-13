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
# STEP 4: LOGIN & REGISTER
# ========================================================
if not st.session_state.logged_in:
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        l_ph = st.text_input("Phone")
        l_pw = st.text_input("Password", type="password")
        if st.button("Login 🚀"):
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
        r_name = st.text_input("Name")
        r_ph = st.text_input("Phone Number")
        r_pw = st.text_input("Password", type="password")
        if st.button("Register ✨"):
            requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_ph(r_ph), "password":r_pw})
            st.success("Registered! Wait for admin.")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR
# ========================================================
u_data = st.session_state.user_data
u_name = u_data.get('Name', 'User')
raw_ph = normalize_ph(u_data.get('Phone', ''))
u_photo = u_data.get('Photo', '')

sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
st.sidebar.markdown(f'<img src="{sidebar_img}" style="width:100px;border-radius:50%">', unsafe_allow_html=True)
st.sidebar.header(u_name)

if st.sidebar.button("🏠 Dashboard"): set_nav("🏠 Dashboard")
if st.sidebar.button("🛍️ New Order"): set_nav("🛍️ New Order")
if st.sidebar.button("📜 History"): set_nav("📜 History")
if st.sidebar.button("💬 Feedback"): set_nav("💬 Feedback")
if raw_ph == normalize_ph(JAZZCASH_NO):
    if st.sidebar.button("🔐 Admin"): set_nav("🔐 Admin")
if st.sidebar.button("Logout 🚪"): st.session_state.clear(); st.rerun()

menu = st.session_state.menu_choice

# ========================================================
# STEP 6: DASHBOARD
# ========================================================
if menu == "🏠 Dashboard":
    st.header("🏠 Dashboard")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    st.metric("Total Bill Paid", f"Rs. {u_ords['Bill'].sum()}")
    st.dataframe(u_ords.tail(5), use_container_width=True)

# ========================================================
# MODULE: NEW ORDER (STEPS 7-13)
# ========================================================
elif menu == "🛍️ New Order":
    # --- STEP 7: Product Selection ---
    st.header("Step 7: Select Product")
    scat = st.selectbox("Category", settings_df['Category'].unique())
    items = settings_df[settings_df['Category'] == scat]
    sprod = st.selectbox("Product", items['Product Name'])
    prc = float(items[items['Product Name'] == sprod]['Price'].values[0])
    qty = st.number_input("Quantity", 1, 100, 1)
    
    if st.button("Add to Cart 🛒"):
        st.session_state.cart.append({"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty})
        st.rerun()

    # --- STEP 8: Cart Review ---
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

        # --- STEP 9: Bill Calculation ---
        st.divider()
        st.header("Step 9: Bill Total")
        final_bill = sum(x['Total'] for x in st.session_state.cart)
        st.subheader(f"Total: Rs. {final_bill}")

        # --- STEP 10: Payment Method ---
        st.divider()
        st.header("Step 10: Select Payment")
        pay_type = st.radio("Method", ["COD", "JazzCash", "EasyPaisa"])

        # --- STEP 11: QR Display ---
        st.divider()
        st.header("Step 11: QR Payment")
        if pay_type != "COD":
            st.write(f"Send to: {JAZZCASH_NO}")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={final_bill}")

        # --- STEP 12: Final Confirmation ---
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

        # --- STEP 13: WhatsApp Link ---
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
# STEP 16: ADMIN PANEL (FIXED)
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Panel")
    ad_tabs = st.tabs(["Orders", "Approvals", "Feedback"])
    
    with ad_tabs[0]:
        st.subheader("All Orders")
        for idx, row in orders_df.iterrows():
            st.write(f"ID: {row['Invoice_ID']} | Status: {row['Status']}")
            if st.button(f"Mark Paid {idx}", key=f"paid_{idx}"):
                requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                st.rerun()

    with ad_tabs[1]:
        st.subheader("Approvals")
        pending_u = users_df[users_df['Role'].str.lower() == 'pending']
        for idx, u in pending_u.iterrows():
            st.write(f"{u['Name']} ({u['Phone']})")
            if st.button(f"Approve {idx}", key=f"app_{idx}"):
                requests.post(SCRIPT_URL, json={"action":"approve_user", "phone":normalize_ph(u['Phone'])})
                st.rerun()

    with ad_tabs[2]:
        st.dataframe(feedback_df)
