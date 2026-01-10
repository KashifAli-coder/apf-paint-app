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
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLQRD3dIUkQbNUi-Blo5WvBYqauD6NgMtYXDsC6-H1JLOgKShx8N5-ASHaNOR-QlOQ/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# --- UI Styling (No Blue Circles) ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #3b82f6; color: white; border: none; }
    .stSidebar { background-color: #ffffff; }
    /* Profile Pic styling without blue circle */
    .profile-img { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 2px solid #eeeeee; }
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
    u_df.columns = [str(c).strip() for c in u_df.columns]
    s_df = pd.read_csv(base + "Settings").fillna('')
    o_df = pd.read_csv(base + "Orders").fillna('')
    f_df = pd.read_csv(base + "Feedback").fillna('')
    return u_df, s_df, o_df, f_df

users_df, settings_df, orders_df, feedback_df = load_all_data()

# ========================================================
# STEP 3: SESSION STATE & HELPERS
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_data': {}, 'cart': [], 'is_admin': False})

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
    
    # Sidebar Profile Image (No blue border)
    sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.sidebar.markdown(f'<div style="text-align:center"><img src="{sidebar_img}" class="profile-img"></div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"<h3 style='text-align: center;'>👤 {u_name}</h3>", unsafe_allow_html=True)
    
    nav = ["👤 Profile", "🛍️ New Order", "📜 History", "💬 Feedback"]
    if st.session_state.is_admin: nav.append("🔐 Admin")
    menu = st.sidebar.radio("Navigation", nav)
    if st.sidebar.button("Logout 🚪"):
        st.session_state.clear(); st.rerun()

# ========================================================
# STEP 6: PROFILE (Fix: Pop-up & Border)
# ========================================================
if menu == "👤 Profile":
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
# STEP 7: ORDER - PRODUCT SELECTION
# ========================================================
elif menu == "🛍️ New Order":
    st.header("🛒 Create New Order")
    
    # Category and Product Selection
    scat = st.selectbox("Category", settings_df['Category'].unique())
    sub_df = settings_df[settings_df['Category'] == scat]
    sprod = st.selectbox("Product", sub_df['Product Name'])
    
    # Price and Quantity
    prc = float(sub_df[sub_df['Product Name'] == sprod]['Price'].values[0])
    qty = st.number_input("Quantity", min_value=1, value=1)
    
    if st.button("Add to Cart ➕", use_container_width=True):
        st.session_state.cart.append({
            "Product": sprod, 
            "Qty": qty, 
            "Price": prc, 
            "Total": prc * qty
        })
        st.toast(f"{sprod} added to cart!")
        st.rerun()

# ========================================================
# STEP 8: ORDER - REVIEW TABLE (Cart Display)
# ========================================================
    if st.session_state.cart:
        st.markdown("### 📋 Review Your Cart")
        
        for i, itm in enumerate(st.session_state.cart):
            col_p, col_q, col_x = st.columns([4, 2, 1])
            col_p.write(f"**{itm['Product']}**")
            col_q.write(f"Rs {int(itm['Total'])} ({itm['Qty']})")
            if col_x.button("❌", key=f"del_cart_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
        st.divider()

# ========================================================
# STEP 9: ORDER - TOTAL BILL & PAYMENT METHOD
# ========================================================
        total_bill = sum(x['Total'] for x in st.session_state.cart)
        st.info(f"#### **Grand Total: Rs. {total_bill}**")
        
        pay_method = st.radio("Select Payment Method", ["COD", "JazzCash", "EasyPaisa"])

# ========================================================
# STEP 10: ORDER - QR CODE GENERATION
# ========================================================
        if pay_method != "COD":
            acc_number = JAZZCASH_NO if pay_method == "JazzCash" else EASYPAISA_NO
            st.warning(f"Pay to {pay_method}: {acc_number}")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-{total_bill}-to-{acc_number}"
            st.image(qr_url, width=150)

# ========================================================
# STEP 11: ORDER - INVOICE PDF GENERATOR
# ========================================================
        def create_pdf_invoice(inv_id, name, items_list, total):
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p.drawString(100, 800, f"Invoice ID: {inv_id}")
            p.drawString(100, 780, f"Customer: {name}")
            p.drawString(100, 760, f"Items: {items_list}")
            p.drawString(100, 740, f"Total Bill: Rs. {total}")
            p.save()
            return buffer.getvalue()

# ========================================================
# STEP 12: ORDER - CONFIRMATION & SAVE TO SHEET
# ========================================================
        if st.button("Confirm Order ✅", use_container_width=True):
            invoice_id = f"APF-{int(time.time())}"
            all_products = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
            
            # Send Data to Google Sheets
            order_payload = {
                "action": "order", 
                "invoice_id": invoice_id,
                "name": u_name, 
                "phone": raw_ph, 
                "product": all_products, 
                "bill": float(total_bill), 
                "payment_method": pay_method
            }
            requests.post(SCRIPT_URL, json=order_payload)
            
            # Generate PDF for Download
            pdf_data = create_pdf_invoice(invoice_id, u_name, all_products, total_bill)
            st.download_button("📥 Download Receipt", pdf_data, file_name=f"{invoice_id}.pdf")
            
            st.session_state.cart = [] # Cart reset
            st.success("Order Placed Successfully!")

# ========================================================
# STEP 13: ORDER - WHATSAPP NOTIFICATION
# ========================================================
            whatsapp_msg = f"*New Order ID:* {invoice_id}\n*Customer:* {u_name}\n*Total:* Rs.{total_bill}"
            wa_link = f"https://wa.me/923005508112?text={requests.utils.quote(whatsapp_msg)}"
            st.markdown(f'<a href="{wa_link}" target="_blank">📲 Send WhatsApp Confirmation</a>', unsafe_allow_html=True)

# ========================================================
# STEP 14: ORDER HISTORY (User Section)
# ========================================================
elif menu == "📜 History":
    st.header("Your Order History")
    user_orders = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    
    if user_orders.empty:
        st.info("No orders found.")
    else:
        st.dataframe(user_orders[['Date', 'Invoice_ID', 'Product', 'Bill', 'Status']], use_container_width=True)

# ========================================================
# STEP 15: FEEDBACK SYSTEM (Auto-Filled)
# ========================================================
elif menu == "💬 Feedback":
    st.header("Share Your Feedback")
    
    # Auto-display user info
    st.text(f"Name: {u_name}")
    st.text(f"Phone: {raw_ph}")
    
    # Active feedback box
    feedback_text = st.text_area("Write your message here...", placeholder="Type your experience...")
    
    if st.button("Submit Feedback 📩"):
        if feedback_text.strip():
            f_payload = {
                "action": "feedback", 
                "name": u_name, 
                "phone": raw_ph, 
                "message": feedback_text
            }
            requests.post(SCRIPT_URL, json=f_payload)
            st.success("Feedback saved to Google Sheet!")
        else:
            st.warning("Please enter a message.")

# ========================================================
# STEP 16: ADMIN PANEL (Management & Approvals)
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Management")
    admin_tab1, admin_tab2 = st.tabs(["📦 Orders Manager", "👥 User Approvals"])
    
    with admin_tab1:
        st.subheader("Manage Active Orders")
        # Pending/Active filter
        pending_orders = orders_df[orders_df['Status'].str.contains("Order|Pending", na=False)]
        
        for idx, row in pending_orders.iterrows():
            with st.expander(f"Order {row['Invoice_ID']} - {row['Name']}"):
                st.write(f"**Items:** {row['Product']} | **Bill:** Rs.{row['Bill']}")
                
                c_paid, c_del = st.columns(2)
                if c_paid.button("Mark Paid ✅", key=f"adm_paid_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "mark_paid", "phone": row['Phone'], "product": row['Product']})
                    st.rerun()
                if c_del.button("Delete 🗑️", key=f"adm_del_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "delete_order", "phone": row['Phone'], "product": row['Product']})
                    st.rerun()

    with admin_tab2:
        st.subheader("New User Requests")
        pending_regs = users_df[users_df['Role'].str.lower() == 'pending']
        
        if pending_regs.empty:
            st.info("No users awaiting approval.")
        else:
            for idx, u_row in pending_regs.iterrows():
                u_ph_clean = normalize_ph(u_row['Phone']) # Formatting fix for .0
                st.write(f"👤 **{u_row['Name']}** ({u_ph_clean})")
                
                if st.button(f"Approve {u_row['Name']} ✅", key=f"adm_app_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "approve_user", "phone": u_ph_clean})
                    st.success(f"{u_row['Name']} has been approved!")
                    time.sleep(1)
                    st.rerun() # Refresh to clear approved user from list
