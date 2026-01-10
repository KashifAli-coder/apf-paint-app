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

# ========================================================
# STEP 2: DATA FETCHING (Bypass Cache for Fresh Data)
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
# STEP 3: SESSION STATE INITIALIZATION
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 
        'user_data': {}, 
        'cart': [], 
        'edit_idx': None, 
        'is_admin': False
    })

# Helper function for phone normalization
def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    if s and not s.startswith('0'):
        return '0' + s
    return s

# ========================================================
# STEP 4: LOGIN & REGISTER (The Secure Fix)
# ========================================================
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        st.subheader("Login to your Account")
        ph_l = st.text_input("Phone Number", key="l_ph").strip()
        pw_l = st.text_input("Password", type="password", key="l_pw").strip()
        
        if st.button("Login 🚀", use_container_width=True):
            u_ph = normalize_ph(ph_l)
            # Data matching with clean columns
            match = users_df[
                (users_df['Phone'].apply(normalize_ph) == u_ph) & 
                (users_df['Password'].astype(str).str.strip() == pw_l)
            ]
            
            if not match.empty:
                user_row = match.iloc[0]
                role = str(user_row.get('Role', '')).strip().lower()
                
                if role == 'pending':
                    st.warning("⏳ Apki dakhust per Amal ho Raha hay account k verify hony ka intizar Karin thanks")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.to_dict()
                    # Admin Logic Fix
                    st.session_state.is_admin = (u_ph == normalize_ph(JAZZCASH_NO))
                    st.success("Login Kamyab!")
                    st.rerun()
            else: 
                st.error("Ghalat Phone ya Password!")

    with tab2:
        st.subheader("Create New Account")
        r_name = st.text_input("Full Name")
        r_ph = st.text_input("Phone Number (0 se shuru karein)")
        r_pw = st.text_input("Create Password", type="password")
        
        if st.button("Register Now ✨", use_container_width=True):
            if r_name and r_ph and r_pw:
                reg_ph = normalize_ph(r_ph)
                already = users_df[users_df['Phone'].apply(normalize_ph) == reg_ph]
                
                if not already.empty:
                    st.error("❌ Ye number pehle se mojud hay.")
                else:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":reg_ph, "password":r_pw})
                    st.success("✅ Registration Successful! Admin approval ka intizar karein.")
            else:
                st.warning("Tamam fields pur karein.")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR & LOGOUT
# ========================================================
else:
    u_name = st.session_state.user_data.get('Name', 'User')
    u_photo = st.session_state.user_data.get('Photo', '')
    raw_ph = normalize_ph(st.session_state.user_data.get('Phone', ''))

    # Sidebar Profile Image Display
    if u_photo and str(u_photo) != 'nan' and str(u_photo).strip() != "":
        st.sidebar.markdown(f'''<div style="text-align:center"><img src="{u_photo}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; border:3px solid #3b82f6;"></div>''', unsafe_allow_html=True)
    else:
        st.sidebar.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    
    st.sidebar.markdown(f"<h3 style='text-align: center;'>👤 {u_name}</h3>", unsafe_allow_html=True)
    
    nav = ["👤 Profile", "🛍️ New Order", "📜 History", "💬 Feedback"]
    if st.session_state.get('is_admin', False): 
        nav.append("🔐 Admin")
    
    menu = st.sidebar.radio("Navigation", nav)
    
    if st.sidebar.button("Logout 🚪", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ========================================================
# STEP 6: USER PROFILE & PHOTO UPLOAD FIX
# ========================================================
if menu == "👤 Profile":
    st.header(f"👋 Hi, {u_name}")
    display_img = u_photo if (u_photo and str(u_photo) != 'nan' and str(u_photo).strip() != "") else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.image(display_img, width=150)

    with st.popover("📷 Change Photo"):
        choice = st.radio("Source:", ["📸 Live Capture", "🖼️ Gallery"])
        img_file = st.camera_input("Take photo") if choice == "📸 Live Capture" else st.file_uploader("Upload", type=["jpg","png","jpeg"])

        if img_file:
            img_bytes = img_file.read()
            b64_data = base64.b64encode(img_bytes).decode('utf-8')
            final_img = f"data:image/png;base64,{b64_data}"
            
            if st.button("Update Now ✅"):
                res = requests.post(SCRIPT_URL, json={"action": "update_photo", "phone": raw_ph, "photo": final_img})
                if "Photo Updated" in res.text:
                    st.session_state.user_data['Photo'] = final_img
                    st.success("Cloud Updated!")
                    st.rerun()
                else: st.error(res.text)

# ========================================================
# STEP 7: ORDER - PRODUCT SELECTION
# ========================================================
elif menu == "🛍️ New Order":
    st.header("🛒 Create New Order")
    scat = st.selectbox("Category", settings_df['Category'].unique())
    sub_df = settings_df[settings_df['Category']==scat]
    sprod = st.selectbox("Product", sub_df['Product Name'])
    prc = float(sub_df[sub_df['Product Name']==sprod]['Price'].values[0])
    
    qty = st.number_input("Quantity", min_value=1, value=1)
    
    if st.button("Add to Cart ➕", use_container_width=True):
        st.session_state.cart.append({"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty})
        st.success(f"{sprod} cart mein shamil ho gaya!")
        st.rerun()

# ========================================================
# STEP 8: ORDER - REVIEW TABLE (Cart Display)
# ========================================================
    if st.session_state.cart:
        st.markdown("### 📋 Review Your Cart")
        for i, itm in enumerate(st.session_state.cart):
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.write(f"**{itm['Product']}** ({itm['Qty']})")
            c2.write(f"Rs {int(itm['Total'])}")
            if c3.button("❌", key=f"del_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
        st.divider()

# ========================================================
# STEP 9: ORDER - TOTAL BILL & PAYMENT METHOD
# ========================================================
        total = sum(x['Total'] for x in st.session_state.cart)
        st.info(f"#### **Grand Total: Rs. {total}**")
        pm = st.radio("Select Payment Method", ["COD", "JazzCash", "EasyPaisa"])

# ========================================================
# STEP 10: ORDER - QR CODE & PAYMENT INFO
# ========================================================
        if pm != "COD":
            acc_no = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
            st.warning(f"Please pay Rs. {total} to {pm} Account: {acc_no}")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Payment-{total}-to-{acc_no}", width=150)

# ========================================================
# STEP 11: ORDER - INVOICE PDF GENERATOR
# ========================================================
        def generate_invoice_pdf(inv, name, items, bill):
            buf = BytesIO()
            p = canvas.Canvas(buf)
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, 800, "ORDER INVOICE")
            p.setFont("Helvetica", 12)
            p.drawString(100, 770, f"Invoice ID: {inv}")
            p.drawString(100, 750, f"Customer: {name}")
            p.drawString(100, 730, f"Total Bill: Rs. {bill}")
            p.drawString(100, 710, f"Items: {items}")
            p.save()
            return buf.getvalue()

# ========================================================
# STEP 12: ORDER - CONFIRMATION & GOOGLE SHEETS SAVE
# ========================================================
        if st.button("Confirm & Place Order ✅", use_container_width=True):
            inv_id = f"APF-{int(time.time())}"
            all_itms = ", ".join([f"{x['Qty']}x {x['Product']}" for x in st.session_state.cart])
            
            # Send to Google Sheets
            payload = {
                "action": "order", 
                "invoice_id": inv_id,
                "name": u_name, 
                "phone": raw_ph, 
                "product": all_itms, 
                "bill": float(total), 
                "payment_method": pm
            }
            requests.post(SCRIPT_URL, json=payload)
            
            # Show PDF Download
            pdf = generate_invoice_pdf(inv_id, u_name, all_itms, total)
            st.download_button("📥 Download PDF Receipt", pdf, file_name=f"{inv_id}.pdf")
            
            st.session_state.cart = [] # Clear cart
            st.success("Order Successfully Placed!")

# ========================================================
# STEP 13: ORDER - WHATSAPP NOTIFICATION
# ========================================================
            wa_msg = f"*New Order Alert!*\nID: {inv_id}\nName: {u_name}\nBill: Rs.{total}"
            wa_url = f"https://wa.me/{JAZZCASH_NO}?text={requests.utils.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank">📲 Notify Admin on WhatsApp</a>', unsafe_allow_html=True)

# ========================================================
# STEP 14: ORDER HISTORY (User Side)
# ========================================================
elif menu == "📜 History":
    st.header("Your Order History")
    # Normalize phone numbers for matching
    my_orders = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    
    if my_orders.empty:
        st.info("Aap ne abhi tak koi order nahi diya.")
    else:
        st.dataframe(my_orders[['Date', 'Invoice_ID', 'Product', 'Bill', 'Status']], use_container_width=True)

# ========================================================
# STEP 15: FEEDBACK SYSTEM
# ========================================================
elif menu == "💬 Feedback":
    st.header("Share Your Feedback")
    f_msg = st.text_area("Write your message here...")
    
    if st.button("Submit Feedback 📩"):
        if f_msg:
            payload = {"action": "feedback", "name": u_name, "phone": raw_ph, "message": f_msg}
            requests.post(SCRIPT_URL, json=payload)
            st.success("Thank you! Aapka feedback record kar liya gaya hai.")
        else:
            st.warning("Message box khali hai.")

# ========================================================
# STEP 16: ADMIN PANEL (Control Center)
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Management")
    ad_tab1, ad_tab2 = st.tabs(["📦 Orders Manager", "👥 User Approvals"])
    
    with ad_tab1:
        # Show only Pending or Active orders
        active_orders = orders_df[orders_df['Status'].str.contains("Order|Pending", na=False)]
        for idx, row in active_orders.iterrows():
            with st.expander(f"Order: {row['Invoice_ID']} - {row['Name']}"):
                st.write(f"**Items:** {row['Product']}")
                st.write(f"**Bill:** Rs. {row['Bill']}")
                
                col_a, col_b = st.columns(2)
                if col_a.button("Mark Paid ✅", key=f"admin_p_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "mark_paid", "phone": row['Phone'], "product": row['Product']})
                    st.rerun()
                if col_b.button("Delete Order 🗑️", key=f"admin_d_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "delete_order", "phone": row['Phone'], "product": row['Product']})
                    st.rerun()

    with ad_tab2:
        # Filter for Pending users
        p_users = users_df[users_df['Role'].str.lower() == 'pending']
        if p_users.empty:
            st.info("Koi naya user pending nahi hai.")
        else:
            for idx, urow in p_users.iterrows():
                st.write(f"**{urow['Name']}** ({urow['Phone']})")
                if st.button(f"Approve {urow['Name']} ✅", key=f"admin_u_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "approve_user", "phone": urow['Phone']})
                    st.success("User Approved!")
                    st.rerun()
