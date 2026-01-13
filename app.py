import streamlit as st
import pd as pd
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
import base64
import time

# ========================================================
# STEP 1: CONFIGURATION & LINKS
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLQRD3dIUkQbNUi-Blo5WvBYqauD6NgMtYXDsC6-H1JLOgKShx8N5-ASHaNOR-QlOQ/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# --- UI Styling ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #3b82f6; color: white; border: none; }
    .stSidebar { background-color: #ffffff; }
    .profile-img { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 2px solid #eeeeee; }
    .alert-box { padding: 15px; border-radius: 10px; background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# Helper Function
def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    if s and not s.startswith('0'): return '0' + s
    return s

# ========================================================
# STEP 2: DATA FETCHING
# ========================================================
@st.cache_data(ttl=0)
def load_all_data():
    t = int(time.time())
    base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
    u_df = pd.read_csv(base + "Users").fillna('')
    u_df.columns = [str(c).strip() for c in u_df.columns]
    s_df = pd.read_csv(base + "Settings").fillna('')
    o_df = pd.read_csv(base + "Orders").fillna('')
    f_df = pd.read_csv(base + "Feedback").fillna('')
    return u_df, s_df, o_df, f_df

users_df, settings_df, orders_df, feedback_df = load_all_data()

# ========================================================
# STEP 3: SESSION STATE & REDIRECTION LOGIC
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'user_data': {}, 'cart': [], 'is_admin': False,
        'menu_choice': "🏠 Dashboard",
        'go_to_dashboard': False  
    })

# Redirection Logic (Error se bachne ke liye index bypass)
if st.session_state.get('go_to_dashboard'):
    st.session_state.menu_choice = "🏠 Dashboard"
    st.session_state.go_to_dashboard = False
    st.rerun()

# ========================================================
# STEP 4: LOGIN & REGISTER (FIXED LINE 62)
# ========================================================
if not st.session_state.logged_in:
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        ph_l = st.text_input("Phone Number", key="l_ph")
        pw_l = st.text_input("Password", type="password", key="l_pw")
        if st.button("Login 🚀"):
            u_ph = normalize_ph(ph_l)
            match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == pw_l)]
            if not match.empty:
                user_row = match.iloc[0]
                if str(user_row['Role']).lower() == 'pending':
                    st.warning("⏳ Account Pending...")
                else:
                    # Logic Fix: Direct update instead of key conflict
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.to_dict()
                    st.session_state.is_admin = (u_ph == normalize_ph(JAZZCASH_NO))
                    st.rerun()
            else: st.error("Invalid Login")
    with t2:
        r_name = st.text_input("Full Name")
        r_ph = st.text_input("Phone")
        r_pw = st.text_input("Create Password", type="password")
        if st.button("Register ✨"):
            requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_ph(r_ph), "password":r_pw})
            st.success("Registered! Wait for approval.")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR
# ========================================================
else:
    u_name = st.session_state.user_data.get('Name', 'User')
    u_photo = st.session_state.user_data.get('Photo', '')
    raw_ph = normalize_ph(st.session_state.user_data.get('Phone', ''))
    
    sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<div style="text-align:center"><img src="{sidebar_img}" class="profile-img"></div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"<h3 style='text-align: center;'>👤 {u_name}</h3>", unsafe_allow_html=True)
    
    nav = ["🏠 Dashboard", "👤 Profile", "🛍️ New Order", "📜 History", "💬 Feedback"]
    if st.session_state.is_admin: nav.append("🔐 Admin")
    
    # Navigation Radio
    menu = st.sidebar.radio("Navigation", nav, key="menu_choice")
    
    if st.sidebar.button("Logout 🚪"):
        st.session_state.clear(); st.rerun()

# ========================================================
# DASHBOARD MODULE
# ========================================================
if menu == "🏠 Dashboard":
    st.header(f"Dashboard - Welcome {u_name}")
    my_orders = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    
    pending = my_orders[my_orders['Status'].str.contains("Order|Pending", case=False, na=False)]
    if not pending.empty:
        st.markdown(f"""
        <div class="alert-box">
            ⚠️ <b>Aapka Order Pending Hai!</b><br>
            Aapke {len(pending)} order(s) abhi approve hona baqi hain.
        </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("Total Orders", len(my_orders))
    c2.metric("Total Bill", f"Rs. {my_orders['Bill'].sum()}")
    st.dataframe(my_orders.tail(5), use_container_width=True)

# ========================================================
# STEP 6: PROFILE 
# ========================================================
elif menu == "👤 Profile":
    st.header(f"👋 Hi, {u_name}")
    p_img = u_photo if (u_photo and str(u_photo) != 'nan') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.markdown(f'<img src="{p_img}" class="profile-img">', unsafe_allow_html=True)
    
    with st.popover("📷 Change Photo"):
        src = st.radio("Choose Source:", ["Select", "📸 Camera", "🖼️ Gallery"], label_visibility="collapsed")
        img_file = None
        if src == "📸 Camera": img_file = st.camera_input("Capture")
        elif src == "🖼️ Gallery": img_file = st.file_uploader("Upload Image")
        
        if img_file:
            b64 = base64.b64encode(img_file.read()).decode('utf-8')
            final = f"data:image/png;base64,{b64}"
            if st.button("Update Now ✅"):
                res = requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":raw_ph, "photo":final})
                if "Photo Updated" in res.text:
                    st.session_state.user_data['Photo'] = final
                    st.success("Updated!"); time.sleep(1); st.rerun()

# ========================================================
# STEP 7-13: ORDERING SYSTEM
# ========================================================
elif menu == "🛍️ New Order":
    st.header("🛒 Create Order")
    scat = st.selectbox("Category", settings_df['Category'].unique())
    sub_df = settings_df[settings_df['Category'] == scat]
    sprod = st.selectbox("Product", sub_df['Product Name'])
    prc = float(sub_df[sub_df['Product Name'] == sprod]['Price'].values[0])
    qty = st.number_input("Quantity", min_value=1, value=1)
    
    if st.button("Add to Cart ➕"):
        st.session_state.cart.append({"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty})
        st.rerun()

    if st.session_state.cart:
        for i, itm in enumerate(st.session_state.cart):
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{itm['Product']}** (Rs. {itm['Total']})")
            if c2.button("❌", key=f"del_{i}"):
                st.session_state.cart.pop(i); st.rerun()

        total_bill = sum(x['Total'] for x in st.session_state.cart)
        st.info(f"#### **Total Bill: Rs. {total_bill}**")

        pay_method = st.radio("Payment Method", ["COD", "JazzCash", "EasyPaisa"])
        if pay_method != "COD":
            acc = JAZZCASH_NO if pay_method == "JazzCash" else EASYPAISA_NO
            st.warning(f"Pay to {pay_method}: {acc}")
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-{total_bill}"
            st.image(qr, width=150)

        if st.button("Confirm Order ✅"):
            inv_id = f"APF-{int(time.time())}"
            prods = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
            requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv_id, "name":u_name, "phone":raw_ph, "product":prods, "bill":float(total_bill), "payment_method":pay_method})
            
            st.session_state.cart = []
            st.success("Order Placed!")
            time.sleep(1)
            st.session_state.go_to_dashboard = True
            st.rerun()

        wa_text = f"New Order: {inv_id}\nTotal: {total_bill}"
        st.markdown(f"[WhatsApp Confirmation](https://wa.me/923005508112?text={wa_text})")

# ========================================================
# STEP 14: HISTORY
# ========================================================
elif menu == "📜 History":
    st.header("History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    st.dataframe(u_ords[['Date', 'Invoice_ID', 'Product', 'Status']], use_container_width=True)

# ========================================================
# STEP 15: FEEDBACK (FIXED LINE 267)
# ========================================================
elif menu == "💬 Feedback":
    st.subheader("🌟 Share Your Feedback")
    f_msg = st.text_area("Message", placeholder="Yahan likhein...", height=150)
    
    if st.button("Submit Feedback 📩"):
        if f_msg.strip():
            with st.spinner("Saving..."):
                payload = {"action": "feedback", "name": u_name, "phone": raw_ph, "message": f_msg, "date": datetime.now().strftime('%Y-%m-%d %H:%M')}
                requests.post(SCRIPT_URL, json=payload)
                st.balloons()
                st.success("✅ Saved! Redirecting...")
                time.sleep(1.5)
                # Redirection Fix
                st.session_state.go_to_dashboard = True
                st.rerun()
        else:
            st.warning("Please type a message.")

# ========================================================
# STEP 16: ADMIN PANEL
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Management Console")
    col_m1, col_m2, col_m3 = st.columns(3)
    total_rev = orders_df[orders_df['Status'].astype(str).str.contains("Paid|Confirmed", na=False)]['Bill'].sum()
    col_m1.metric("Total Revenue", f"Rs. {total_rev}")
    col_m2.metric("Total Orders", len(orders_df))
    col_m3.metric("Active Users", len(users_df[users_df['Role'].str.lower() == 'user']))
    
    tab_ord, tab_usr, tab_fdb = st.tabs(["📦 Orders", "👥 Users", "💬 Feedback"])
    with tab_ord:
        active_o = orders_df[orders_df['Status'].str.contains("Order|Pending", na=False)]
        for idx, r in active_o.iterrows():
            with st.expander(f"Order {r['Invoice_ID']}"):
                st.write(f"Products: {r['Product']}")
                if st.button("Mark Paid ✅", key=f"p_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "mark_paid", "phone": normalize_ph(r['Phone']), "product": r['Product']})
                    st.rerun()
    with tab_usr:
        p_users = users_df[users_df['Role'].str.lower() == 'pending']
        for idx, ur in p_users.iterrows():
            st.write(f"👤 {ur['Name']}")
            if st.button(f"Approve {ur['Name']}", key=f"u_{idx}"):
                requests.post(SCRIPT_URL, json={"action": "approve_user", "phone": normalize_ph(ur['Phone'])})
                st.rerun()
    with tab_fdb:
        st.dataframe(feedback_df)
