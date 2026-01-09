import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas

# ========================================================
# STEP 1: CONFIGURATION & LINKS
# ========================================================
SHEET_ID = ""
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwr65rLmMBi8gMtIT6JAeHbD4keI7Er_05EKlJdUOmVh7WKzTwoZ37-Pxii96XCcYo/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# ========================================================
# STEP 2: DATA FETCHING (4 Tables from 1 Sheet)
# ========================================================
@st.cache_data(ttl=60)
def load_all_data():
    base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    u_df = pd.read_csv(base + "Users")
    s_df = pd.read_csv(base + "Settings")
    o_df = pd.read_csv(base + "Orders")
    f_df = pd.read_csv(base + "Feedback")
    return u_df, s_df, o_df, f_df

users_df, settings_df, orders_df, feedback_df = load_all_data()

# ========================================================
# STEP 3: SESSION STATE INITIALIZATION
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_data': {}, 'cart': [], 'edit_idx': None})

# ========================================================
# STEP 4: LOGIN LOGIC
# ========================================================
if not st.session_state.logged_in:
    st.header("🔐 APF Login")
    ph = st.text_input("Phone Number")
    pw = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        user = users_df[(users_df['Phone'].astype(str) == ph) & (users_df['Password'].astype(str) == pw)]
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.user_data = user.iloc[0].to_dict()
            st.session_state.is_admin = (ph == "03005508112")
            st.rerun()
    st.stop()

# ========================================================
# STEP 5: SIDEBAR & LOGOUT
# ========================================================
else:
    u_name = st.session_state.user_data['Name']
    st.sidebar.success(f"👤 {u_name}")
    nav = ["👤 Profile", "🛍️ New Order", "📜 History", "💬 Feedback"]
    if st.session_state.is_admin: nav.append("🔐 Admin")
    menu = st.sidebar.radio("Navigation", nav)
    if st.sidebar.button("Logout 🚪", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ========================================================
# STEP 6: USER PROFILE DASHBOARD
# ========================================================
    if menu == "👤 Profile":
        st.header(f"👋 Welcome, {u_name}")
        st.metric("Phone", st.session_state.user_data['Phone'])
        st.info("Select 'New Order' from Sidebar to shop.")

# ========================================================
# STEP 7: ORDER - PRODUCT SELECTION
# ========================================================
    elif menu == "🛍️ New Order":
        st.header("🛒 Create New Order")
        scat = st.selectbox("Category", settings_df['Category'].unique())
        sprod = st.selectbox("Product", settings_df[settings_df['Category']==scat]['Product Name'])
        prc = float(settings_df[settings_df['Product Name']==sprod]['Price'].values[0])
        
        dq = st.session_state.cart[st.session_state.edit_idx]['Qty'] if st.session_state.edit_idx is not None else 1
        qty = st.number_input("Quantity", min_value=1, value=dq)
        
        if st.button("Update Item ✏️" if st.session_state.edit_idx is not None else "Add to Cart ➕", use_container_width=True):
            item = {"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty}
            if st.session_state.edit_idx is not None:
                st.session_state.cart[st.session_state.edit_idx] = item
                st.session_state.edit_idx = None
            else: st.session_state.cart.append(item)
            st.rerun()

# ========================================================
# STEP 8: ORDER - REVIEW TABLE (Original Design)
# ========================================================
        if st.session_state.cart:
            st.markdown("### 📋 Review Cart")
            st.markdown('<div style="background:#3b82f6; color:white; padding:10px; border-radius:5px; display:flex; justify-content:space-between; font-weight:bold;"><span>Product (Qty)</span><span>Total</span><span>Actions</span></div>', unsafe_allow_html=True)
            for i, itm in enumerate(st.session_state.cart):
                c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
                c1.write(f"**{itm['Product']}** ({itm['Qty']})")
                c2.write(f"Rs {int(itm['Total'])}")
                if c3.button("✏️", key=f"e_{i}"):
                    st.session_state.edit_idx = i
                    st.rerun()
                if c4.button("❌", key=f"x_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
                st.divider()

# ========================================================
# STEP 9: ORDER - TOTAL BILL & PAYMENT
# ========================================================
            total = sum(x['Total'] for x in st.session_state.cart)
            st.success(f"**Grand Total: Rs. {total}**")
            pm = st.radio("Payment", ["COD", "JazzCash", "EasyPaisa"])

# ========================================================
# STEP 10: ORDER - QR CODE GENERATION
# ========================================================
            if pm != "COD":
                acc = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
                st.info(f"Pay to {pm}: {acc}")
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=Pay-{total}", width=120)

# ========================================================
# STEP 11: INVOICE GENERATION (PDF)
# ========================================================
            def get_pdf(inv, name, items, bill):
                buf = BytesIO()
                p = canvas.Canvas(buf)
                p.drawString(100, 800, f"Invoice: {inv} | Customer: {name}")
                p.drawString(100, 780, f"Items: {items} | Total: Rs. {bill}")
                p.save()
                return buf.getvalue()

# ========================================================
# STEP 12: ORDER CONFIRMATION & SAVE
# ========================================================
            inv_id = f"APF-{len(orders_df) + 1:04d}"
            if st.button(f"Confirm Order ({inv_id})", use_container_width=True):
                all_itms = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
                requests.post(SCRIPT_URL, json={"action":"order", "name":u_name, "phone":st.session_state.user_data['Phone'], "product":all_itms, "bill":float(total), "payment_method":pm, "invoice_id": inv_id})
                
                # Download Button for PDF
                pdf_file = get_pdf(inv_id, u_name, all_itms, total)
                st.download_button("📥 Download Receipt", pdf_file, f"{inv_id}.pdf")

# ========================================================
# STEP 13: WHATSAPP NOTIFICATION
# ========================================================
                wa_msg = f"*New Order ID:* {inv_id}\n*Customer:* {u_name}"
                wa_url = f"https://wa.me/923005508112?text={requests.utils.quote(wa_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background:#25D366; color:white; width:100%; padding:10px; border:none; border-radius:5px;">Notify Admin</button></a>', unsafe_allow_html=True)
                st.session_state.cart = []
                st.rerun()

# ========================================================
# STEP 14: ORDER HISTORY
# ========================================================
    elif menu == "📜 History":
        st.header("Your Order History")
        my_orders = orders_df[orders_df['Phone'].astype(str) == str(st.session_state.user_data['Phone'])]
        st.table(my_orders[['Date', 'Invoice_ID', 'Product', 'Status']])

# ========================================================
# STEP 15: FEEDBACK SYSTEM
# ========================================================
    elif menu == "💬 Feedback":
        st.header("Send Feedback")
        msg = st.text_area("Message")
        if st.button("Submit Feedback"):
            requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":st.session_state.user_data['Phone'], "message":msg})
            st.success("Sent Successfully!")

# ========================================================
# STEP 16: ADMIN PANEL (Management Logic)
# ========================================================
    elif menu == "🔐 Admin":
        st.header("Admin Control")
        p_orders = orders_df[orders_df['Status'].str.contains("Order|Pending", na=False)]
        for idx, row in p_orders.iterrows():
            with st.expander(f"Order: {row['Invoice_ID']}"):
                st.write(f"Items: {row['Product']}")
                c1, c2 = st.columns(2)
                if c1.button("Mark Paid ✅", key=f"p_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "phone":row['Phone'], "product":row['Product']})
                    st.rerun()
                if c2.button("Delete 🗑️", key=f"d_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"delete_order", "phone":row['Phone'], "product":row['Product']})
                    st.rerun()
