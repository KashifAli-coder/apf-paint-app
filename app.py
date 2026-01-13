import streamlit as st
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
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLQRD3dIUkQbNUi-Blo5WvBYqauD6NgMtYXDsC6-H1JLOgKShx8Y5-ASHaNOR-QlOQ/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# UI Styling
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #3b82f6; color: white; border: none; }
    .profile-img { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 2px solid #eeeeee; }
    .alert-box { padding: 15px; border-radius: 10px; background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; margin-bottom: 20px; }
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

users_df, settings_df, orders_df, feedback_df = load_all_data()

# ========================================================
# STEP 3: SESSION STATE & HELPERS
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'user_data': {}, 'cart': [], 'is_admin': False,
        'menu_choice': "🏠 Dashboard" 
    })

def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    if s and not s.startswith('0'): return '0' + s
    return s

# ========================================================
# STEP 4: LOGIN & REGISTER
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
                    st.session_state.update({'logged_in': True, 'user_data': user_row.to_dict(), 'is_admin': (u_ph == normalize_ph(JAZZCASH_NO))})
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
    
    menu = st.sidebar.radio("Navigation", nav, key="menu_choice")
    
    if st.sidebar.button("Logout 🚪"):
        st.session_state.clear(); st.rerun()

# ========================================================
# DASHBOARD MODULE (With Pending Order Alert)
# ========================================================
if menu == "🏠 Dashboard":
    st.header(f"Dashboard - {u_name}")
    my_orders = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    
    # ALERT BOX FOR PENDING ORDERS
    pending = my_orders[my_orders['Status'].str.contains("Order|Pending", case=False, na=False)]
    if not pending.empty:
        st.markdown(f"""
        <div class="alert-box">
            ⚠️ <b>Aapka Order Pending Hai!</b><br>
            Aapke {len(pending)} order(s) abhi tak approve nahi hue. Payment confirm hote hi status update ho jayega.
        </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("Total Orders", len(my_orders))
    c2.metric("Total Bill", f"Rs. {my_orders['Bill'].sum()}")
    
    st.subheader("Your Order History")
    if my_orders.empty: st.info("Koi order record nahi mila.")
    else: st.dataframe(my_orders.tail(5)[['Date', 'Invoice_ID', 'Status']], use_container_width=True)

# ========================================================
# STEP 6: PROFILE
# ========================================================
elif menu == "👤 Profile":
    st.header(f"👋 Profile - {u_name}")
    p_img = u_photo if (u_photo and str(u_photo) != 'nan') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.markdown(f'<img src="{p_img}" class="profile-img">', unsafe_allow_html=True)
    
    with st.popover("📷 Photo Update"):
        img_file = st.file_uploader("New Photo")
        if img_file:
            b64 = base64.b64encode(img_file.read()).decode('utf-8')
            final = f"data:image/png;base64,{b64}"
            if st.button("Save ✅"):
                requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":raw_ph, "photo":final})
                st.session_state.user_data['Photo'] = final
                st.success("Updated!"); st.rerun()

# ========================================================
# STEP 7: ORDER - PRODUCT SELECTION
# ========================================================
elif menu == "🛍️ New Order":
    st.header("🛒 Place Your Order")
    scat = st.selectbox("Select Category", settings_df['Category'].unique())
    sub_df = settings_df[settings_df['Category'] == scat]
    sprod = st.selectbox("Select Product", sub_df['Product Name'])
    prc = float(sub_df[sub_df['Product Name'] == sprod]['Price'].values[0])
    qty = st.number_input("How many?", min_value=1, value=1)
    
    if st.button("Add to Cart 🛒"):
        st.session_state.cart.append({"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty})
        st.toast(f"{sprod} Added!")
        st.rerun()

# ========================================================
# STEP 8: ORDER - REVIEW TABLE
# ========================================================
    if st.session_state.cart:
        st.markdown("### 📋 Your Selection")
        for i, itm in enumerate(st.session_state.cart):
            c_p, c_q, c_x = st.columns([4, 2, 1])
            c_p.write(f"**{itm['Product']}**")
            c_q.write(f"Rs {int(itm['Total'])}")
            if c_x.button("❌", key=f"del_{i}"):
                st.session_state.cart.pop(i); st.rerun()

# ========================================================
# STEP 9: ORDER - TOTAL CALCULATION
# ========================================================
        total_bill = sum(x['Total'] for x in st.session_state.cart)
        st.info(f"#### **Grand Total: Rs. {total_bill}**")

# ========================================================
# STEP 10: ORDER - PAYMENT & QR
# ========================================================
        pay_method = st.radio("Choose Payment Method", ["COD", "JazzCash", "EasyPaisa"])
        if pay_method != "COD":
            acc = JAZZCASH_NO if pay_method == "JazzCash" else EASYPAISA_NO
            st.warning(f"Pay to {acc}")
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-{total_bill}"
            st.image(qr, width=150)

# ========================================================
# STEP 11: ORDER - INVOICE PDF FUNCTION
# ========================================================
        def generate_pdf(inv_id, name, items, total):
            buf = BytesIO()
            p = canvas.Canvas(buf)
            p.drawString(100, 800, f"Invoice ID: {inv_id}")
            p.drawString(100, 780, f"Customer: {name}")
            p.drawString(100, 760, f"Items: {items}")
            p.drawString(100, 740, f"Total: Rs. {total}")
            p.save()
            return buf.getvalue()

# ========================================================
# STEP 12: ORDER - CONFIRMATION & REDIRECT
# ========================================================
        if st.button("Order Confirm Karein ✅"):
            inv_id = f"APF-{int(time.time())}"
            prods = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
            
            # API Call
            requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv_id, "name":u_name, "phone":raw_ph, "product":prods, "bill":float(total_bill), "payment_method":pay_method})
            
            # Clear Cart and Set Dashboard
            st.session_state.cart = []
            st.session_state.menu_choice = "🏠 Dashboard" 
            st.success("Mubarak ho! Order ho gaya.")
            time.sleep(1.5)
            st.rerun()

# ========================================================
# STEP 13: ORDER - WHATSAPP NOTIFICATION
# ========================================================
            whatsapp_msg = f"*New Order:* {inv_id}\n*Customer:* {u_name}\n*Total:* Rs.{total_bill}"
            wa_link = f"https://wa.me/923005508112?text={requests.utils.quote(whatsapp_msg)}"
            st.markdown(f'<a href="{wa_link}" target="_blank">📲 Send WhatsApp Confirmation</a>', unsafe_allow_html=True)

# ========================================================
# STEP 14: ORDER HISTORY
# ========================================================
elif menu == "📜 History":
    st.header("Order History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    st.dataframe(u_ords[['Date', 'Invoice_ID', 'Product', 'Bill', 'Status']], use_container_width=True)

# ========================================================
# STEP 15: FEEDBACK (With Dashboard Redirect Fix)
# ========================================================
elif menu == "💬 Feedback":
    st.subheader("🌟 Share Your Feedback")
    
    # Message box
    f_msg = st.text_area("Message", placeholder="Yahan apna tajurba likhein...", height=150, key="f_input")
    
    if st.button("Submit Feedback 📩", use_container_width=True):
        if st.session_state.f_input.strip():
            with st.spinner("Processing..."):
                payload = {
                    "action": "feedback", 
                    "name": u_name, 
                    "phone": raw_ph, 
                    "message": st.session_state.f_input,
                    "date": datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                requests.post(SCRIPT_URL, json=payload)
                
                st.balloons()
                st.success("✅ Saved! Dashboard par wapsi ho rahi hai...")
                
                # Sab se zaroori fix: Line 249-270 error handling
                st.session_state.f_input = "" 
                st.session_state.menu_choice = "🏠 Dashboard" 
                
                time.sleep(1.5)
                st.rerun()
        else:
            st.warning("⚠️ Message likhna zaroori hai.")

# ========================================================
# STEP 16: UPDATED ADMIN PANEL & DASHBOARD
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Management Console")
    
    with st.container():
        st.markdown("### 📊 Business Overview")
        col_m1, col_m2, col_m3 = st.columns(3)
        
        total_rev = orders_df[orders_df['Status'].astype(str).str.contains("Paid|Confirmed", na=False)]['Bill'].sum()
        total_ord = len(orders_df)
        active_usr = len(users_df[users_df['Role'].astype(str).str.lower() == 'user'])
        
        col_m1.metric("Total Revenue", f"Rs. {total_rev}")
        col_m2.metric("Total Orders", total_ord)
        col_m3.metric("Active Users", active_usr)
        
        if not orders_df.empty:
            sales_chart_df = orders_df.copy()
            sales_chart_df['Date'] = pd.to_datetime(sales_chart_df['Date']).dt.date
            chart_group = sales_chart_df.groupby('Date')['Bill'].sum().reset_index()
            st.line_chart(chart_group.set_index('Date'))
        st.divider()

    tab_ord, tab_usr, tab_fdb = st.tabs(["📦 Orders Manager", "👥 User Approvals", "💬 Feedback Logs"])
    
    with tab_ord:
        st.subheader("Manage Active Orders")
        active_o = orders_df[orders_df['Status'].astype(str).str.contains("Order|Pending", na=False)]
        if active_o.empty:
            st.info("No active orders found.")
        else:
            for idx, r in active_o.iterrows():
                with st.expander(f"Order {r['Invoice_ID']} - {r['Name']}"):
                    st.write(f"**Products:** {r['Product']}")
                    st.write(f"**Bill:** Rs.{r['Bill']} | **Method:** {r['Payment_Method']}")
                    
                    c_p, c_d = st.columns(2)
                    if c_p.button("Mark Paid ✅", key=f"btn_p_{idx}"):
                        requests.post(SCRIPT_URL, json={"action": "mark_paid", "phone": normalize_ph(r['Phone']), "product": r['Product']})
                        st.rerun()
                    if c_d.button("Delete 🗑️", key=f"btn_d_{idx}"):
                        requests.post(SCRIPT_URL, json={"action": "delete_order", "phone": normalize_ph(r['Phone']), "product": r['Product']})
                        st.rerun()

    with tab_usr:
        st.subheader("User Verification")
        p_users = users_df[users_df['Role'].astype(str).str.lower() == 'pending']
        if p_users.empty:
            st.info("No pending approvals.")
        else:
            for idx, ur in p_users.iterrows():
                u_ph_formatted = normalize_ph(ur['Phone'])
                st.write(f"👤 **{ur['Name']}** ({u_ph_formatted})")
                if st.button(f"Approve {ur['Name']} ✅", key=f"btn_u_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "approve_user", "phone": u_ph_formatted})
                    st.success(f"{ur['Name']} approved!")
                    time.sleep(1)
                    st.rerun()

    with tab_fdb:
        st.subheader("Customer Reviews")
        if feedback_df.empty:
            st.info("No feedback messages yet.")
        else:
            st.dataframe(feedback_df[['Date', 'Name', 'Phone', 'Message']], use_container_width=True)
