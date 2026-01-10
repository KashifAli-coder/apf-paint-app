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
# STEP 15: FANCY FEEDBACK SYSTEM (Auto-Reset & Redirect)
# ========================================================
elif menu == "💬 Feedback":
    st.subheader("🌟 Share Your Experience")
    
    # 1. Session State Initialize (Text area ko khali karne ke liye)
    if 'feedback_text' not in st.session_state:
        st.session_state.feedback_text = ""

    # Custom Fancy Card for User Info
    st.markdown(f"""
    <div style="background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #f1f5f9; margin-bottom: 20px;">
        <div style="color: #64748b; font-size: 0.9em; margin-bottom: 5px;">Customer Name</div>
        <div style="color: #1e293b; font-weight: 600; font-size: 1.1em; margin-bottom: 15px;">👤 {u_name}</div>
        <div style="color: #64748b; font-size: 0.9em; margin-bottom: 5px;">Phone Number</div>
        <div style="color: #1e293b; font-weight: 600; font-size: 1.1em; margin-bottom: 15px;">📞 {raw_ph}</div>
        <div style="color: #64748b; font-size: 0.9em; margin-bottom: 5px;">Current Date</div>
        <div style="color: #1e293b; font-weight: 600; font-size: 1.1em;">📅 {datetime.now().strftime('%d %b, %Y')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Text Area connected to Session State
    st.markdown("##### ✍️ Write your message")
    f_msg = st.text_area(
        "feedback_box", 
        value=st.session_state.feedback_text,
        placeholder="Type your experience or suggestions here...", 
        height=150, 
        label_visibility="collapsed",
        key="f_input" # Unique key for state management
    )
    
    if st.button("Submit Feedback 📩", use_container_width=True):
        if f_msg.strip():
            with st.spinner("Saving your feedback..."):
                payload = {
                    "action":"feedback", 
                    "name":u_name, 
                    "phone":raw_ph, 
                    "message":f_msg,
                    "date": datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                # Google Sheets Update
                requests.post(SCRIPT_URL, json=payload)
                
                # Feedback Effects
                st.balloons()
                st.success("✅ Thank you! Your feedback has been saved.")
                
                # 3. Logic: Clear Box and Move to Dashboard
                time.sleep(1.5) # User ko success message dekhne ka mauka dein
                st.session_state.feedback_text = "" # Box khali karein
                
                # Sidebar menu ko "Dashboard" par redirect karne ke liye
                # Note: 'Dashboard' wahi spelling honi chahiye jo aapke sidebar radio button mein hai
                if 'menu' in st.session_state:
                    st.session_state.menu = "🏠 Dashboard" # Menu index reset (Aapka Dashboard icon ke mutabiq)
                
                st.rerun() # Refresh karke Dashboard par bhej dein
        else:
            st.warning("⚠️ Please type a message before submitting.")


# ========================================================
# STEP 16: UPDATED ADMIN PANEL & DASHBOARD (Integrated)
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Management Console")
    
    # --- DASHBOARD: Analytics Metrics (Integrated as Step 16 Part) ---
    with st.container():
        st.markdown("### 📊 Business Overview")
        col_m1, col_m2, col_m3 = st.columns(3)
        
        # Calculations for metrics
        total_rev = orders_df[orders_df['Status'].astype(str).str.contains("Paid|Confirmed", na=False)]['Bill'].sum()
        total_ord = len(orders_df)
        active_usr = len(users_df[users_df['Role'].astype(str).str.lower() == 'user'])
        
        col_m1.metric("Total Revenue", f"Rs. {total_rev}")
        col_m2.metric("Total Orders", total_ord)
        col_m3.metric("Active Users", active_usr)
        
        # Sales Chart Visualization
        if not orders_df.empty:
            sales_chart_df = orders_df.copy()
            sales_chart_df['Date'] = pd.to_datetime(sales_chart_df['Date']).dt.date
            chart_group = sales_chart_df.groupby('Date')['Bill'].sum().reset_index()
            st.line_chart(chart_group.set_index('Date'))
        st.divider()

    # --- MANAGEMENT: Action Tabs ---
    tab_ord, tab_usr, tab_fdb = st.tabs(["📦 Orders Manager", "👥 User Approvals", "💬 Feedback Logs"])
    
    with tab_ord:
        st.subheader("Manage Active Orders")
        # Filter for orders that need attention
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
                u_ph_formatted = normalize_ph(ur['Phone']) # Fix for .0 formatting
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

# ========================================================
# STEP 16: UPDATED ADMIN PANEL & DASHBOARD (Integrated)
# ========================================================
elif menu == "🔐 Admin":
    st.header("🛡️ Admin Management Console")
    
    # --- DASHBOARD: Analytics Metrics (Integrated as Step 16 Part) ---
    with st.container():
        st.markdown("### 📊 Business Overview")
        col_m1, col_m2, col_m3 = st.columns(3)
        
        # Calculations for metrics
        total_rev = orders_df[orders_df['Status'].astype(str).str.contains("Paid|Confirmed", na=False)]['Bill'].sum()
        total_ord = len(orders_df)
        active_usr = len(users_df[users_df['Role'].astype(str).str.lower() == 'user'])
        
        col_m1.metric("Total Revenue", f"Rs. {total_rev}")
        col_m2.metric("Total Orders", total_ord)
        col_m3.metric("Active Users", active_usr)
        
        # Sales Chart Visualization
        if not orders_df.empty:
            sales_chart_df = orders_df.copy()
            sales_chart_df['Date'] = pd.to_datetime(sales_chart_df['Date']).dt.date
            chart_group = sales_chart_df.groupby('Date')['Bill'].sum().reset_index()
            st.line_chart(chart_group.set_index('Date'))
        st.divider()

    # --- MANAGEMENT: Action Tabs ---
    tab_ord, tab_usr, tab_fdb = st.tabs(["📦 Orders Manager", "👥 User Approvals", "💬 Feedback Logs"])
    
    with tab_ord:
        st.subheader("Manage Active Orders")
        # Filter for orders that need attention
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
                u_ph_formatted = normalize_ph(ur['Phone']) # Fix for .0 formatting
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
