import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from reportlab.pdfgen import canvas

# ==========================================
# STEP 1: CONFIGURATION & DATA FETCHING
# ==========================================
# In settings ko aap apne mutabiq change kar sakte hain
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxvtcxSnzQ11cCpkEQbb7-wvacH6LYjw7XldVfxORmgFpooxk4UKBsKFYZNueKhTWLe/exec" 
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# Data Fetching (Assuming CSV or API)
@st.cache_data(ttl=60)
def load_data():
    # Yahan aapki sheets se data load hoga
    users_df = pd.read_csv("users.csv") # Example
    settings_df = pd.read_csv("settings.csv") # Example
    orders_df = pd.read_csv("orders.csv") # Example
    return users_df, settings_df, orders_df

users_df, settings_df, orders_df = load_data()

# ==========================================
# STEP 2: SESSION & LOGIN LOGIC
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.header("🔐 Login")
    phone = st.text_input("Phone Number")
    pw = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        user = users_df[(users_df['Phone'] == phone) & (users_df['Password'] == pw)]
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.user_data = user.iloc[0].to_dict()
            st.session_state.is_admin = (phone == "03005508112")
            st.session_state.cart = []
            st.rerun()
        else:
            st.error("Ghalat Details!")
    st.stop()

# ==========================================
# STEP 3: SIDEBAR NAVIGATION
# ==========================================
else:
    u_name = st.session_state.user_data.get('Name', 'User')
    st.sidebar.success(f"👤 Welcome: {u_name}")
    
    menu = st.sidebar.radio("Navigation", ["👤 Profile", "🛍️ New Order", "📜 History", "🔐 Admin"] if st.session_state.is_admin else ["👤 Profile", "🛍️ New Order", "📜 History"])
    
    if st.sidebar.button("Logout 🚪", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ==========================================
# STEP 4: USER DASHBOARD (PROFILE)
# ==========================================
    if menu == "👤 Profile":
        st.header(f"👋 Welcome, {u_name}")
        st.subheader("Your Dashboard")
        c1, c2 = st.columns(2)
        c1.metric("Phone", st.session_state.user_data['Phone'])
        c2.metric("Orders", len(orders_df[orders_df['Phone']==st.session_state.user_data['Phone']]))

# ==========================================
# STEP 5: NEW ORDER (CART & INLINE TABLE)
# ==========================================
    elif menu == "🛍️ New Order":
        st.header("🛒 Create New Order")
        
        # Product Selection
        cat = st.selectbox("Category", settings_df['Category'].unique())
        prod = st.selectbox("Product", settings_df[settings_df['Category']==cat]['Product Name'])
        price = float(settings_df[settings_df['Product Name']==prod]['Price'].values[0])
        
        if 'e_idx' not in st.session_state: st.session_state.e_idx = None
        def_q = st.session_state.cart[st.session_state.e_idx]['Qty'] if st.session_state.e_idx is not None else 1
        qty = st.number_input("Quantity", min_value=1, value=def_q)
        
        if st.button("Add to Cart ➕" if st.session_state.e_idx is None else "Update Item ✏️", use_container_width=True):
            item = {"Product": prod, "Qty": qty, "Total": price * qty, "Price": price}
            if st.session_state.e_idx is not None:
                st.session_state.cart[st.session_state.e_idx] = item
                st.session_state.e_idx = None
            else:
                st.session_state.cart.append(item)
            st.rerun()

        # Original Table Design (No Blue Boxes, Inline Icons)
        if st.session_state.cart:
            st.markdown("### 📋 Review Items")
            st.markdown('<div style="background:#3b82f6; color:white; padding:10px; border-radius:5px; display:flex; justify-content:space-between; font-weight:bold; font-size:14px;"><span>Product (Qty)</span><span>Total</span><span>Actions</span></div>', unsafe_allow_html=True)

            for i, itm in enumerate(st.session_state.cart):
                col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
                col1.write(f"**{itm['Product']}** ({itm['Qty']})")
                col2.write(f"Rs {int(itm['Total'])}")
                if col3.button("✏️", key=f"ed_{i}"):
                    st.session_state.e_idx = i
                    st.rerun()
                if col4.button("❌", key=f"dl_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
                st.divider()

# ==========================================
# STEP 6: PAYMENT METHOD & QR CODE
# ==========================================
            total = sum(i['Total'] for i in st.session_state.cart)
            st.success(f"**Total Bill: Rs. {total}**")
            pm = st.radio("Payment Method", ["COD", "JazzCash", "EasyPaisa"])
            if pm != "COD":
                acc = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
                st.info(f"Transfer to {pm}: {acc}")
                qr = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-{total}-to-{acc}"
                st.image(qr, width=120)

# ==========================================
# STEP 7: ORDER CONFIRMATION & NOTIFICATION
# ==========================================
            inv = f"APF-{len(orders_df) + 1:04d}"
            if st.button(f"Confirm Order ({inv})", use_container_width=True):
                items_txt = ", ".join([f"{i['Qty']}x {i['Product']}" for i in st.session_state.cart])
                # Post to Google Sheet
                requests.post(SCRIPT_URL, json={"action":"order", "name":u_name, "phone":st.session_state.user_data['Phone'], "product":items_txt, "bill":float(total), "payment_method":pm, "invoice_id": inv})
                
                st.success(f"Order Success! ID: {inv}")
                
                # Step 8: PDF Receipt
                pdf = BytesIO()
                p = canvas.Canvas(pdf)
                p.drawString(100, 750, f"Invoice: {inv}")
                p.drawString(100, 730, f"Customer: {u_name}")
                p.drawString(100, 710, f"Total: Rs. {total}")
                p.save()
                st.download_button("📥 Download Receipt", pdf.getvalue(), f"{inv}.pdf")
                
                # Step 9: WhatsApp Notification
                wa_msg = f"*New Order ID:* {inv}\n*Bill:* Rs. {total}"
                wa_url = f"https://wa.me/923005508112?text={requests.utils.quote(wa_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:12px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer;">💬 Notify Admin</button></a>', unsafe_allow_html=True)
                
                st.session_state.cart = []
                st.rerun()

# ==========================================
# STEP 10: ADMIN PANEL (MARK PAID / DELETE)
# ==========================================
    elif menu == "🔐 Admin":
        st.header("Admin Control")
        pending = orders_df[orders_df['Status'].str.contains("Order|Pending", na=False)]
        for idx, row in pending.iterrows():
            with st.expander(f"Order: {row['Invoice_ID']} - {row['Name']}"):
                st.write(f"Items: {row['Product']} | Bill: {row['Bill']}")
                c1, c2 = st.columns(2)
                if c1.button("Mark Paid ✅", key=f"p_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "phone":row['Phone'], "product":row['Product']})
                    st.rerun()
                if c2.button("Delete 🗑️", key=f"d_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"delete_order", "phone":row['Phone'], "product":row['Product']})
                    st.rerun()
