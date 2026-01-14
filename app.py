import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# 1. DATABASE & API CONFIGURATION
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# QR Code Links
JAZZCASH_QR = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={JAZZCASH_NO}"
EASYPAISA_QR = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={EASYPAISA_NO}"

st.set_page_config(page_title="Paint Pro Store - Full System", layout="wide", initial_sidebar_state="expanded")

# ========================================================
# 2. ADVANCED CSS CUSTOMIZATION
# ========================================================
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #f4f7f9; }
    
    /* Dashboard Metric Cards */
    .metric-container { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 25px; }
    .m-card {
        flex: 1; min-width: 200px; padding: 25px; border-radius: 20px; text-align: center; color: white;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05); transition: 0.3s;
    }
    .m-card:hover { transform: translateY(-5px); }
    .c-total { background: linear-gradient(135deg, #1e3a8a, #3b82f6); }
    .c-pending { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
    .c-complete { background: linear-gradient(135deg, #059669, #10b981); }
    .c-active { background: linear-gradient(135deg, #7c3aed, #a78bfa); }
    
    /* Buttons Styling */
    .stButton>button {
        border-radius: 12px; font-weight: 700; height: 3.2em;
        transition: all 0.4s ease; border: none;
    }
    
    /* Activity Rows */
    .order-row {
        background: white; padding: 22px; border-radius: 18px; margin-bottom: 15px;
        border-left: 6px solid #3b82f6; display: flex; justify-content: space-between;
        align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    /* QR Box Styling */
    .qr-container {
        text-align: center; background: #ffffff; padding: 25px;
        border: 2px solid #e2e8f0; border-radius: 25px; margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. CORE DATA ENGINE
# ========================================================
@st.cache_data(ttl=2)
def load_factory_data():
    try:
        t_stamp = int(time.time())
        base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t_stamp}&sheet="
        u_df = pd.read_csv(base_url + "Users").fillna('')
        s_df = pd.read_csv(base_url + "Settings").fillna('')
        o_df = pd.read_csv(base_url + "Orders").fillna('')
        f_df = pd.read_csv(base_url + "Feedback").fillna('')
        return u_df, s_df, o_df, f_df
    except Exception as e:
        st.error(f"Data loading failed: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_db, settings_db, orders_db, feedback_db = load_factory_data()

def clean_phone(p_num):
    s = str(p_num).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def get_new_invoice_id(df):
    if df.empty or 'Invoice_ID' not in df.columns: return "0001"
    try:
        max_id = pd.to_numeric(df['Invoice_ID'], errors='coerce').max()
        return f"{int(max_id) + 1:04d}" if not pd.isna(max_id) else "0001"
    except: return "0001"

# ========================================================
# 4. SESSION STATE CONTROLLER
# ========================================================
if 'auth_status' not in st.session_state: st.session_state.auth_status = False
if 'current_user' not in st.session_state: st.session_state.current_user = {}
if 'active_tab' not in st.session_state: st.session_state.active_tab = "🏠 Dashboard"
if 'order_wizard_active' not in st.session_state: st.session_state.order_wizard_active = False
if 'step_number' not in st.session_state: st.session_state.step_number = 1
if 'order_buffer' not in st.session_state: st.session_state.order_buffer = {}
if 'show_success_msg' not in st.session_state: st.session_state.show_success_msg = False

def change_screen(new_screen):
    st.session_state.active_tab = new_screen
    st.rerun()

# ========================================================
# 5. AUTHENTICATION (LOGIN/SIGNUP)
# ========================================================
if not st.session_state.auth_status:
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🎨 Paint Pro Portal</h1>", unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["🔐 Secure Login", "📝 New Registration"])
        
        with login_tab:
            phone_input = st.text_input("Mobile Number", key="login_ph")
            pass_input = st.text_input("Password", type="password", key="login_pw")
            if st.button("Enter Dashboard 🚀", use_container_width=True):
                target_ph = clean_phone(phone_input)
                match = users_db[(users_db['Phone'].apply(clean_phone) == target_ph) & (users_db['Password'].astype(str) == pass_input)]
                if not match.empty:
                    st.session_state.auth_status = True
                    st.session_state.current_user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid credentials provided.")
        
        with signup_tab:
            reg_name = st.text_input("Full Name")
            reg_ph = st.text_input("Mobile Number")
            reg_pass = st.text_input("Create Password", type="password")
            if st.button("Submit Registration ✨", use_container_width=True):
                if reg_name and reg_ph and reg_pass:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":reg_name, "phone":clean_phone(reg_ph), "password":reg_pass})
                    st.success("Registration sent for approval!")
                else: st.error("Please fill all fields.")
    st.stop()

# ========================================================
# 6. SIDEBAR NAVIGATION
# ========================================================
u_info = st.session_state.current_user
u_name, u_phone = u_info.get('Name', 'User'), clean_phone(u_info.get('Phone', ''))
u_img = u_info.get('Photo', "https://cdn-icons-png.flaticon.com/512/149/149071.png")

with st.sidebar:
    st.markdown(f'''
        <div style="text-align:center; padding: 20px;">
            <img src="{u_img}" style="width:130px; height:130px; border-radius:50%; object-fit:cover; border:4px solid #3b82f6;">
            <h2 style="margin-top:15px;">{u_name}</h2>
            <p style="color:#64748b;">Member ID: {u_phone}</p>
        </div>
    ''', unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Factory Dashboard", use_container_width=True): change_screen("🏠 Dashboard")
    if st.button("🛍️ Create New Order", use_container_width=True, type="primary"): 
        st.session_state.order_wizard_active = True
        st.session_state.step_number = 1
        st.rerun()
    if st.button("📜 My Order History", use_container_width=True): change_screen("📜 History")
    if st.button("👤 Profile Settings", use_container_width=True): change_screen("👤 Profile")
    if st.button("💬 Give Feedback", use_container_width=True): change_screen("💬 Feedback")
    
    if u_phone == clean_phone(JAZZCASH_NO):
        st.divider()
        if st.button("🔐 Admin Control", use_container_width=True): change_screen("🔐 Admin")
        
    st.divider()
    if st.button("Logout System 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()

# ========================================================
# 7. REAL LOOK ORDER WIZARD (With Verification)
# ========================================================
if st.session_state.order_wizard_active:
    @st.dialog("🛒 Secure Order Booking")
    def run_order_wizard():
        step = st.session_state.step_number
        st.progress(step / 5)
        st.write(f"Phase {step} of 5")

        if step == 1:
            st.subheader("Step 1: Product Selection")
            categories = list(settings_db['Category'].unique())
            sel_cat = st.selectbox("Product Category", categories)
            products = list(settings_db[settings_db['Category'] == sel_cat]['Product Name'].unique())
            sel_prod = st.selectbox("Product Name", products)
            if st.button("Go to Customization ➡️", use_container_width=True):
                st.session_state.order_buffer.update({"cat": sel_cat, "prod": sel_prod})
                st.session_state.step_number = 2; st.rerun()

        elif step == 2:
            st.subheader("Step 2: Specifications")
            p_rec = settings_db[settings_db['Product Name'] == st.session_state.order_buffer['prod']].iloc[0]
            shades = [c.split(':')[0] for c in str(p_rec['Colors']).split(',') if c.strip()]
            sel_shade = st.selectbox("Select Shade", shades)
            
            sizes = [p for p in ["20kg", "Gallon", "Quarter"] if float(p_rec.get(f"Price_{p}", 0)) > 0]
            sel_size = st.radio("Select Size", sizes, horizontal=True)
            sel_qty = st.number_input("Quantity", 1, 5000, 1)
            
            unit_price = float(p_rec.get(f"Price_{sel_size}", 0))
            bill_total = unit_price * sel_qty
            st.info(f"Subtotal: Rs. {bill_total}")
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.step_number = 1; st.rerun()
            if c2.button("Next: Payment ➡️"):
                st.session_state.order_buffer.update({"shade": sel_shade, "size": sel_size, "qty": sel_qty, "total": bill_total})
                st.session_state.step_number = 3; st.rerun()

        elif step == 3:
            st.subheader("Step 3: Payment Method")
            pay_mode = st.selectbox("Method", ["JazzCash", "EasyPaisa", "COD"])
            st.write("📌 *Note: Online payment ke liye confirmation zaroori hai.*")
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.step_number = 2; st.rerun()
            if c2.button("Continue ➡️"):
                st.session_state.order_buffer['method'] = pay_mode
                st.session_state.step_number = 4 if pay_mode != "COD" else 5
                st.rerun()

        elif step == 4:
            st.subheader("Step 4: Secure Payment Verification")
            method = st.session_state.order_buffer['method']
            qr_path = JAZZCASH_QR if method == "JazzCash" else EASYPAISA_QR
            phone_path = JAZZCASH_NO if method == "JazzCash" else EASYPAISA_NO
            
            st.markdown(f"""
                <div class="qr-container">
                    <h4 style='color:#1e40af;'>Scan to Pay via {method}</h4>
                    <img src="{qr_path}" width="200">
                    <h2 style="color:#1e40af; margin:15px 0;">Rs. {st.session_state.order_buffer['total']}</h2>
                    <div style="background:#f8fafc; padding:15px; border-radius:12px; border:1px solid #e2e8f0;">
                        <small>Account Number:</small><br>
                        <b style="font-size:20px;">{phone_path}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("📸 **Verify Transaction**")
            proof = st.file_uploader("Upload Payment Screenshot", type=['jpg','png','jpeg'])
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.step_number = 3; st.rerun()
            if proof:
                if c2.button("Final Review 🔍"): st.session_state.step_number = 5; st.rerun()
            else:
                st.warning("Please upload screenshot to proceed.")

        elif step == 5:
            st.subheader("Step 5: Review & Submit")
            data = st.session_state.order_buffer
            st.markdown(f"""
                **Product:** {data['prod']} ({data['size']})<br>
                **Shade:** {data['shade']}<br>
                **Qty:** {data['qty']}<br>
                <hr>
                <h3 style='color:#1e3a8a;'>Total: Rs. {data['total']}</h3>
                **Payment:** {data['method']} (Receipt Uploaded)
            """, unsafe_allow_html=True)
            
            if st.button("Final Submit Order ✅", type="primary", use_container_width=True):
                with st.spinner("Recording Order..."):
                    new_inv = get_new_invoice_id(orders_db)
                    prod_str = f"{data['qty']}x {data['prod']} ({data['size']}) - {data['shade']}"
                    requests.post(SCRIPT_URL, json={
                        "action":"order", "invoice_id":new_inv, "name":u_name, "phone":u_phone, 
                        "product":prod_str, "bill":data['total'], "payment_method":data['method']
                    })
                    st.session_state.order_wizard_active = False
                    st.session_state.show_success_msg = True; st.rerun()
    run_order_wizard()

# --- SUCCESS FEEDBACK ---
if st.session_state.show_success_msg:
    @st.dialog("✅ Order Recorded")
    def notify_success():
        st.success("Aapka order mehfooz kar liya gaya hai!")
        st.info("Hum jald hi aapki payment aur screenshot verify karke order process karenge. Shukriya!")
        if st.button("Ok, Go to Dashboard", use_container_width=True):
            st.session_state.show_success_msg = False
            change_screen("🏠 Dashboard")
    notify_success()

# ========================================================
# 8. MAIN DASHBOARD MODULE (Updated with 4 Cards)
# ========================================================
if st.session_state.active_tab == "🏠 Dashboard":
    st.markdown(f"## 🏠 Factory Overview")
    user_orders = orders_db[orders_db['Phone'].apply(clean_phone) == u_phone]
    
    # Calculate Data for Cards
    total_orders = len(user_orders)
    pending_orders = len(user_orders[user_orders['Status'].str.contains('Pending|Process', case=False)])
    complete_orders = len(user_orders[user_orders['Status'].str.contains('Paid|Complete', case=False)])
    store_members = len(users_db)

    st.markdown(f'''
        <div class="metric-container">
            <div class="m-card c-total"><small>MY TOTAL ORDERS</small><h3>{total_orders}</h3></div>
            <div class="m-card c-pending"><small>PENDING</small><h3>{pending_orders}</h3></div>
            <div class="m-card c-complete"><small>COMPLETED</small><h3>{complete_orders}</h3></div>
            <div class="m-card c-active"><small>STORE MEMBERS</small><h3>{store_members}</h3></div>
        </div>
    ''', unsafe_allow_html=True)
    
    st.subheader("🕒 Recent Activity")
    if not user_orders.empty:
        for _, row in user_orders.tail(5).iloc[::-1].iterrows():
            st.markdown(f'''
                <div class="order-row">
                    <div><b>{row["Product"]}</b><br><small>{row["Timestamp"]}</small></div>
                    <div style="text-align:right;"><b>Rs. {row["Bill"]}</b><br><span style="color:#2563eb;">{row["Status"]}</span></div>
                </div>
            ''', unsafe_allow_html=True)
    else: st.info("Abhi tak koi order nahi kiya gaya.")

# ========================================================
# 9. PROFILE & SECURITY
# ========================================================
elif st.session_state.active_tab == "👤 Profile":
    st.header("👤 Profile & Security")
    st.markdown(f'''
        <div style="text-align:center; background:white; padding:40px; border-radius:30px; border:1px solid #e2e8f0;">
            <img src="{u_img}" style="width:160px; height:160px; border-radius:50%; object-fit:cover; border:5px solid #3b82f6; margin-bottom:20px;">
            <h2>{u_name}</h2>
            <p>Contact: {u_phone}</p>
        </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("🔐 Change Password"):
            old_p = st.text_input("Current Password", type="password")
            new_p = st.text_input("New Secure Password", type="password")
            if st.button("Confirm Password Change"):
                if old_p == str(u_info['Password']):
                    requests.post(SCRIPT_URL, json={"action":"update_password", "phone":u_phone, "password":new_p})
                    st.success("Password Updated! Logging out..."); time.sleep(2)
                    st.session_state.clear(); st.rerun()
                else: st.error("Old password is incorrect.")
                
    with col2:
        with st.expander("🖼️ Update Photo"):
            f_up = st.file_uploader("Choose New Photo", type=['jpg','png'])
            if f_up and st.button("Upload Now"):
                b64_img = f"data:image/png;base64,{base64.b64encode(f_up.read()).decode()}"
                requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":u_phone, "photo":b64_img})
                st.success("Photo Updated!"); time.sleep(1); st.rerun()

# ========================================================
# 10. OTHER MODULES
# ========================================================
elif st.session_state.active_tab == "📜 History":
    st.header("📜 Complete History")
    hist_df = orders_db[orders_db['Phone'].apply(clean_phone) == u_phone]
    st.dataframe(hist_df.iloc[::-1], use_container_width=True, hide_index=True)

elif st.session_state.active_tab == "🔐 Admin":
    st.header("🛡️ Factory Admin Control")
    tab1, tab2 = st.tabs(["🛒 All Orders", "👥 User Database"])
    with tab1:
        for idx, r in orders_db.iloc[::-1].iterrows():
            with st.expander(f"Order #{r['Invoice_ID']} - {r['Name']}"):
                st.write(f"Product: {r['Product']}")
                st.write(f"Payment: {r['Payment_Method']}")
                if st.button("Approve & Mark Paid ✅", key=f"adm_p_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":r['Invoice_ID']})
                    st.rerun()
    with tab2: st.dataframe(users_db, use_container_width=True)

elif st.session_state.active_tab == "💬 Feedback":
    st.header("💬 Feedback")
    fb_txt = st.text_area("Hamein batayein hamari service kaisi lagi?")
    if st.button("Submit Feedback"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":u_phone, "message":fb_txt})
        st.success("Shukriya! Aapka feedback wasool ho gaya.")
