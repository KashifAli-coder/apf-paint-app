import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
import streamlit as st
import base64
import requests


# ========================================================
# STEP 1: CONFIGURATION & LINKS
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLQRD3dIUkQbNUi-Blo5WvBYqauD6NgMtYXDsC6-H1JLOgKShx8N5-ASHaNOR-QlOQ/exec"
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
# STEP 4: LOGIN & REGISTER (The Secure & Robust Way)
# ========================================================
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    # Number normalization: 0 handle karne ke liye
    def normalize_ph(n):
        s = str(n).strip().replace('.0', '')
        if s and not s.startswith('0'):
            return '0' + s
        return s

    with tab1:
        st.subheader("Login to your Account")
        ph_l = st.text_input("Phone Number", key="l_ph").strip()
        pw_l = st.text_input("Password", type="password", key="l_pw").strip()
        
        if st.button("Login 🚀", use_container_width=True):
            # 1. Column cleaning to avoid KeyError
            temp_df = users_df.copy().fillna('')
            temp_df.columns = [str(c).strip() for c in temp_df.columns]
            
            if 'Phone' not in temp_df.columns:
                st.error("Sheet Error: 'Phone' column nahi mila. Headers check karein.")
            else:
                u_ph = normalize_ph(ph_l)
                # Data matching
                match = temp_df[
                    (temp_df['Phone'].apply(normalize_ph) == u_ph) & 
                    (temp_df['Password'].astype(str).str.strip() == pw_l)
                ]
                
                if not match.empty:
                    user_row = match.iloc[0]
                    role = str(user_row['Role']).strip().lower()
                    if role in ['pending', '']:
                        st.warning("⏳ Apki dakhust per Amal ho Raha hay account k verify hony ka intizar Karin thanks")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_row.to_dict()
                        st.session_state.is_admin = (u_ph == "03005508112")
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
                # 1. Columns clean karein (Line 89 Fix)
                temp_df = users_df.copy().fillna('')
                temp_df.columns = [str(c).strip() for c in temp_df.columns]
                
                reg_ph = normalize_ph(r_ph)
                
                # 2. Duplicate Check: Kya ye number pehle se sheet mein hai?
                already = temp_df[temp_df['Phone'].apply(normalize_ph) == reg_ph]
                
                if not already.empty:
                    current_status = str(already.iloc[0]['Role']).strip().lower()
                    if current_status in ['pending', '']:
                        st.info("⏳ Apki dakhust pehle se moosool ho chuki hay aur Pending hay. Intezar karein.")
                    else:
                        st.error("❌ Ye number pehle se Active hay. Meharbani farmakar Login karein.")
                else:
                    # Nayi dakhust bhejna
                    requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":reg_ph, "password":r_pw})
                    st.success("✅ Registration Successful! Admin approval ka intizar karein.")
                    st.balloons()
            else:
                st.warning("Tamam fields pur karein.")
    st.stop()


# ========================================================
# >>> START: STEP 5 (SIDEBAR & LOGOUT) <<<
# ========================================================
else:
    u_name = st.session_state.user_data.get('Name', 'User')
    u_photo = st.session_state.user_data.get('Photo', '')
    raw_ph = str(st.session_state.user_data.get('Phone', '')).strip().replace('.0', '')
    display_ph = raw_ph if raw_ph.startswith('0') else '0' + raw_ph

    # --- SIDEBAR PROFILE DISPLAY ---
    if u_photo and str(u_photo) != 'nan' and str(u_photo).strip() != "":
        st.sidebar.markdown(f'''
            <div style="display: flex; justify-content: center;">
                <img src="{u_photo}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; border:3px solid #3b82f6;">
            </div>
        ''', unsafe_allow_html=True)
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
# >>> START: STEP 6 (USER PROFILE & POP-UP) <<<
# ========================================================
if menu == "👤 Profile":
    st.header(f"👋 Hi, {u_name}")
    
    # --- CSS Section ---
    st.markdown("""
    <style>
    .profile-container { position: relative; width: 150px; margin: auto; display: block; }
    .main-profile-pic { 
        width: 150px; height: 150px; border-radius: 50%; object-fit: cover; 
        border: 2px solid #eeeeee; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); 
    }
    </style>
    """, unsafe_allow_html=True)

    # Image Display
    display_img = u_photo if (u_photo and str(u_photo) != 'nan' and str(u_photo).strip() != "") else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    
    st.markdown(f'<div class="profile-container"><img src="{display_img}" class="main-profile-pic"></div>', unsafe_allow_html=True)

    # Popover Button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.popover("📷 Change Photo", use_container_width=True):
            choice = st.radio("Choose Source:", ["Select Option", "📸 Live Capture", "🖼️ Gallery"], label_visibility="collapsed")
            
            img_file = None
            if choice == "📸 Live Capture":
                img_file = st.camera_input("Take a photo")
            elif choice == "🖼️ Gallery":
                img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

            if img_file:
                    import base64
                    img_bytes = img_file.read()
                    b64_data = base64.b64encode(img_bytes).decode('utf-8')
                    final_img = f"data:image/png;base64,{b64_data}"
                    
                    if st.button("Update Now ✅", use_container_width=True):
                        try:
                            with st.spinner("Saving to Cloud..."):
                                payload = {
                                    "action": "update_photo", 
                                    "phone": raw_ph, 
                                    "photo": final_img
                                }
                                response = requests.post(SCRIPT_URL, json=payload)
                                
                                # App Script se "Photo Updated" ka jawab aana chahiye
                                if "Photo Updated" in response.text:
                                    st.session_state.user_data['Photo'] = final_img
                                    st.success("Profile Photo Saved in Cloud!")
                                    st.rerun()
                                else:
                                    st.error(f"Server Error: {response.text}")
                        except Exception as e:
                            st.error(f"Connection error: {e}")

# ========================================================
# STEP 7: ORDER - PRODUCT SELECTION (Indentation Fixed)
# ========================================================
elif menu == "🛍️ New Order":  # <--- Yeh line 'if' ke bilkul niche honi chahiye
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
        else: 
            st.session_state.cart.append(item)
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
# STEP 16: ADMIN PANEL (Order Management & User Approval)
# ========================================================
    elif menu == "🔐 Admin":
        st.header("🛡️ Admin Control Center")
        
        # Tabs for better organization
        tab_ord, tab_usr = st.tabs(["🛍️ Manage Orders", "👥 Approve New Users"])
        
        # --- SUB-STEP 16A: ORDER MANAGEMENT ---
        with tab_ord:
            st.subheader("Pending Orders")
            # Sirf wo orders jin ka status Pending ya Order ho
            p_orders = orders_df[orders_df['Status'].str.contains("Order|Pending", na=False)]
            
            if p_orders.empty:
                st.info("Abhi koi naya order nahi aaya.")
            else:
                for idx, row in p_orders.iterrows():
                    with st.expander(f"📦 Order: {row['Invoice_ID']} - {row['Name']}"):
                        st.write(f"**Items:** {row['Product']}")
                        st.write(f"**Bill:** Rs. {row['Bill']} | **Phone:** {row['Phone']}")
                        st.write(f"**Payment:** {row['Payment']}")
                        
                        c1, c2 = st.columns(2)
                        # Mark Paid Button
                        if c1.button("Mark Paid ✅", key=f"p_{idx}"):
                            requests.post(SCRIPT_URL, json={
                                "action": "mark_paid", 
                                "phone": row['Phone'], 
                                "product": row['Product']
                            })
                            st.success("Status Updated!")
                            st.rerun()
                        
                        # Delete Order Button
                        if c2.button("Delete 🗑️", key=f"d_{idx}"):
                            requests.post(SCRIPT_URL, json={
                                "action": "delete_order", 
                                "phone": row['Phone'], 
                                "product": row['Product']
                            })
                            st.warning("Order Deleted!")
                            st.rerun()

        # --- SUB-STEP 16B: USER APPROVAL SYSTEM ---
        with tab_usr:
            st.subheader("Registration Requests")
            pending_users = users_df[users_df['Role'].str.lower() == 'pending']
            
            if pending_users.empty:
                st.info("Koi naya user approval ke liye nahi hai.")
            else:
                for idx, urow in pending_users.iterrows():
                    # Checkbox for selection
                    confirm = st.checkbox(f"Approve {urow['Name']} ({urow['Phone']})", key=f"chk_{idx}")
                    
                    if confirm:
                        if st.button(f"Confirm Activation for {urow['Name']} ✅", key=f"btn_app_{idx}"):
                            requests.post(SCRIPT_URL, json={
                                "action": "approve_user", 
                                "phone": urow['Phone']
                            })
                            st.success(f"{urow['Name']} active ho gaya hai!")
                            st.rerun()
                st.divider()
