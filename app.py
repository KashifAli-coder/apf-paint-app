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

# --- UI Styling ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; height: 40px; }
    .profile-img { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; display: block; margin: 0 auto; border: 2px solid #3b82f6; }
    .status-paid { color: green; font-weight: bold; }
    .status-pending { color: orange; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ========================================================
# STEP 2: DATA FETCHING
# ========================================================
@st.cache_data(ttl=0)
def load_all_data():
    t = int(time.time())
    base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
    u_df = pd.read_csv(base + "Users").fillna('')
    s_df = pd.read_csv(base + "Settings").fillna('')
    o_df = pd.read_csv(base + "Orders").fillna('')
    f_df = pd.read_csv(base + "Feedback").fillna('')
    return u_df, s_df, o_df, f_df

def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    if s and not s.startswith('0'): return '0' + s
    return s

users_df, settings_df, orders_df, feedback_df = load_all_data()

# ========================================================
# STEP 3: SESSION STATE & NAVIGATION LOGIC
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
# STEP 5: SIDEBAR (NO RADIO LOCK)
# ========================================================
u_data = st.session_state.user_data
u_name = u_data.get('Name', 'User')
raw_ph = normalize_ph(u_data.get('Phone', ''))
u_photo = u_data.get('Photo', '')

sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
st.sidebar.markdown(f'<img src="{sidebar_img}" class="profile-img">', unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='text-align:center;'>{u_name}</h3>", unsafe_allow_html=True)

if st.sidebar.button("🏠 Dashboard"): set_nav("🏠 Dashboard")
if st.sidebar.button("👤 Profile"): set_nav("👤 Profile")
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
# STEP 7: PRODUCT SELECTION
# ========================================================
elif menu == "🛍️ New Order":
    st.header("🛒 Select Products")
    cat = st.selectbox("Category", settings_df['Category'].unique())
    items = settings_df[settings_df['Category'] == cat]
    prod = st.selectbox("Product", items['Product Name'])
    price = float(items[items['Product Name'] == prod]['Price'].values[0])
    qty = st.number_input("Qty", 1, 50, 1)
    
    if st.button("Add to Cart 🛒"):
        st.session_state.cart.append({"Product": prod, "Qty": qty, "Price": price, "Total": price*qty})
        st.toast("Added!")

# ========================================================
# STEP 8: CART REVIEW
# ========================================================
    if st.session_state.cart:
        st.subheader("Your Cart")
        for i, itm in enumerate(st.session_state.cart):
            st.write(f"{itm['Qty']}x {itm['Product']} - Rs.{itm['Total']}")
            if st.button("Remove ❌", key=f"rm_{i}"):
                st.session_state.cart.pop(i); st.rerun()

# ========================================================
# STEP 9: BILL CALCULATION
# ========================================================
        total_bill = sum(x['Total'] for x in st.session_state.cart)
        st.info(f"**Total Amount: Rs. {total_bill}**")

# ========================================================
# STEP 10: PAYMENT METHOD
# ========================================================
        pmode = st.radio("Payment Method", ["COD", "JazzCash", "EasyPaisa"])

# ========================================================
# STEP 11: QR DISPLAY
# ========================================================
        if pmode != "COD":
            st.warning(f"Pay to: {JAZZCASH_NO}")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-{total_bill}")

# ========================================================
# STEP 12: ORDER CONFIRMATION (Action Module)
# ========================================================
        if st.button("Confirm Order ✅"):
            inv = f"INV-{int(time.time())}"
            summary = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
            requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv, "name":u_name, "phone":raw_ph, "product":summary, "bill":total_bill, "payment_method":pmode})
            st.session_state.cart = []
            st.success("Order Placed!")
            time.sleep(1)
            set_nav("🏠 Dashboard")

# ========================================================
# STEP 13: WHATSAPP LINK
# ========================================================
        st.markdown(f"[📲 Send Receipt via WhatsApp](https://wa.me/923005508112?text=Order-{u_name})")

# ========================================================
# STEP 14: HISTORY
# ========================================================
elif menu == "📜 History":
    st.header("📜 My Orders")
    st.dataframe(orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph], use_container_width=True)

# ========================================================
# STEP 15: FEEDBACK
# ========================================================
elif menu == "💬 Feedback":
    st.header("💬 Feedback")
    f_msg = st.text_area("Message")
    if st.button("Submit"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":raw_ph, "message":f_msg})
        st.success("Thank you!"); time.sleep(1); set_nav("🏠 Dashboard")

# ========================================================
# STEP 16: ADMIN PANEL (FIXED & COMPLETE)
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Panel")
    t_ord, t_usr, t_fdb = st.tabs(["Orders", "Approvals", "Feedback"])
    
    with t_ord:
        pending_o = orders_df[orders_df['Status'].str.contains("Order|Pending", na=False)]
        for i, r in pending_o.iterrows():
            with st.expander(f"Order: {r['Invoice_ID']} - {r['Name']}"):
                st.write(f"Product: {r['Product']} | Bill: {r['Bill']}")
                if st.button("Mark Paid ✅", key=f"p_{i}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "phone":normalize_ph(r['Phone']), "product":r['Product']})
                    st.rerun()
                if st.button("Delete 🗑️", key=f"d_{i}"):
                    requests.post(SCRIPT_URL, json={"action":"delete_order", "phone":normalize_ph(r['Phone']), "product":r['Product']})
                    st.rerun()

    with t_usr:
        p_users = users_df[users_df['Role'].str.lower() == 'pending']
        for i, u in p_users.iterrows():
            st.write(f"👤 {u['Name']} ({u['Phone']})")
            if st.button("Approve User ✅", key=f"au_{i}"):
                requests.post(SCRIPT_URL, json={"action":"approve_user", "phone":normalize_ph(u['Phone'])})
                st.rerun()

    with t_fdb:
        st.dataframe(feedback_df, use_container_width=True)
