import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# 1. CONFIGURATION & PERMANENT LINKS
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# QR Image Links (Google se generate kiye gaye temporary QR codes)
JAZZCASH_QR = "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=03005508112"
EASYPAISA_QR = "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=03005508112"

st.set_page_config(page_title="Paint Pro Store - Full Version", layout="wide", initial_sidebar_state="expanded")

# ========================================================
# 2. ADVANCED PROFESSIONAL CSS
# ========================================================
st.markdown("""
    <style>
    /* Global Styles */
    .stApp { background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stButton>button { border-radius: 10px; font-weight: 700; height: 3em; transition: 0.4s; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 2px solid #e1e4e8; }
    
    /* Dashboard Metric Cards (Original Gradients) */
    .card-container { display: flex; gap: 20px; margin-bottom: 25px; }
    .card-blue {
        flex: 1; background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        color: white; padding: 25px; border-radius: 18px; text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .card-green {
        flex: 1; background: linear-gradient(135deg, #064e3b, #10b981);
        color: white; padding: 25px; border-radius: 18px; text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .card-orange {
        flex: 1; background: linear-gradient(135deg, #7c2d12, #f97316);
        color: white; padding: 25px; border-radius: 18px; text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Order Activity Rows */
    .order-row {
        background: white; padding: 20px; border-radius: 15px; margin-bottom: 15px;
        border: 1px solid #e5e7eb; display: flex; justify-content: space-between;
        align-items: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* QR Display Box */
    .qr-container {
        text-align: center; background: #ffffff; padding: 20px;
        border: 3px dashed #3b82f6; border-radius: 20px; margin: 15px 0;
    }
    
    /* Profile Header */
    .profile-card {
        text-align: center; background: white; padding: 40px;
        border-radius: 25px; border: 1px solid #e5e7eb; margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. CORE LOGIC & DATA SYNC
# ========================================================
@st.cache_data(ttl=2)
def fetch_data():
    try:
        t = int(time.time())
        url_base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
        users = pd.read_csv(url_base + "Users").fillna('')
        settings = pd.read_csv(url_base + "Settings").fillna('')
        orders = pd.read_csv(url_base + "Orders").fillna('')
        feedback = pd.read_csv(url_base + "Feedback").fillna('')
        return users, settings, orders, feedback
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_db, settings_db, orders_db, feedback_db = fetch_data()

def normalize_phone(p):
    s = str(p).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def generate_invoice_id(df):
    if df.empty or 'Invoice_ID' not in df.columns: return "0001"
    try:
        nums = pd.to_numeric(df['Invoice_ID'], errors='coerce').dropna()
        return f"{int(nums.max()) + 1:04d}" if not nums.empty else "0001"
    except: return f"{len(df)+1:04d}"

# ========================================================
# 4. SESSION MANAGEMENT
# ========================================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = {}
if 'page' not in st.session_state: st.session_state.page = "🏠 Dashboard"
if 'wizard_open' not in st.session_state: st.session_state.wizard_open = False
if 'w_step' not in st.session_state: st.session_state.w_step = 1
if 'draft_order' not in st.session_state: st.session_state.draft_order = {}
if 'success_popup' not in st.session_state: st.session_state.success_popup = False

def nav_to(p):
    st.session_state.page = p
    st.rerun()

# ========================================================
# 5. AUTHENTICATION MODULE
# ========================================================
if not st.session_state.logged_in:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🎨 Paint Pro Factory</h1>", unsafe_allow_html=True)
        login_tab, reg_tab = st.tabs(["🔐 Login Account", "📝 Register New"])
        
        with login_tab:
            l_ph = st.text_input("Phone Number", placeholder="03XXXXXXXXX")
            l_pw = st.text_input("Password", type="password")
            if st.button("Sign In 🚀", use_container_width=True):
                u_ph = normalize_phone(l_ph)
                user = users_db[(users_db['Phone'].apply(normalize_phone) == u_ph) & (users_db['Password'].astype(str) == l_pw)]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid Phone or Password.")
        
        with reg_tab:
            r_name = st.text_input("Full Name")
            r_ph = st.text_input("Phone Number")
            r_pw = st.text_input("Set Password", type="password")
            if st.button("Create Account ✨", use_container_width=True):
                if r_name and r_ph and r_pw:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_phone(r_ph), "password":r_pw})
                    st.success("Registration request sent! Wait for approval.")
                else: st.error("Please fill all details.")
    st.stop()

# ========================================================
# 6. SIDEBAR NAVIGATION
# ========================================================
u_info = st.session_state.user_data
u_name, u_phone = u_info.get('Name', 'User'), normalize_phone(u_info.get('Phone', ''))
u_pic = u_info.get('Photo', "https://cdn-icons-png.flaticon.com/512/149/149071.png")

with st.sidebar:
    st.markdown(f'''
        <div style="text-align:center; padding: 10px;">
            <img src="{u_pic}" style="width:120px; height:120px; border-radius:50%; object-fit:cover; border:4px solid #3b82f6;">
            <h2 style="margin-top:10px;">{u_name}</h2>
            <p style="color:gray;">{u_phone}</p>
        </div>
    ''', unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Dashboard", use_container_width=True): nav_to("🏠 Dashboard")
    if st.button("🛍️ New Order", use_container_width=True, type="primary"):
        st.session_state.wizard_open = True
        st.session_state.w_step = 1
        st.rerun()
    if st.button("📜 History", use_container_width=True): nav_to("📜 History")
    if st.button("👤 Profile", use_container_width=True): nav_to("👤 Profile")
    if st.button("💬 Feedback", use_container_width=True): nav_to("💬 Feedback")
    
    if u_phone == normalize_phone(JAZZCASH_NO):
        st.divider()
        if st.button("🔐 Admin Control", use_container_width=True): nav_to("🔐 Admin")
    
    st.divider()
    if st.button("Logout 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()

# ========================================================
# 7. STEP-BY-STEP POPUP WIZARD (QR INCLUDED)
# ========================================================
if st.session_state.wizard_open:
    @st.dialog("🎯 Order Process Wizard")
    def start_wizard():
        step = st.session_state.w_step
        st.markdown(f"**Progress: Step {step} of 5**")
        st.progress(step / 5)

        if step == 1:
            st.subheader("Select Product Category")
            all_cats = list(settings_db['Category'].unique())
            scat = st.selectbox("Category", all_cats)
            available_prods = list(settings_db[settings_db['Category'] == scat]['Product Name'].unique())
            sprod = st.selectbox("Select Product", available_prods)
            if st.button("Next: Specs ➡️", use_container_width=True):
                st.session_state.draft_order.update({"cat": scat, "prod": sprod})
                st.session_state.w_step = 2; st.rerun()

        elif step == 2:
            st.subheader("Shade & Quantity")
            p_details = settings_db[settings_db['Product Name'] == st.session_state.draft_order['prod']].iloc[0]
            shades = [c.split(':')[0] for c in str(p_details['Colors']).split(',') if c.strip()]
            sel_shade = st.selectbox("Choose Shade", shades)
            
            pack_options = [p for p in ["20kg", "Gallon", "Quarter"] if float(p_details.get(f"Price_{p}", 0)) > 0]
            sel_size = st.radio("Packing Size", pack_options, horizontal=True)
            sel_qty = st.number_input("How many units?", 1, 1000, 1)
            
            u_price = float(p_details.get(f"Price_{sel_size}", 0))
            total_amt = u_price * sel_qty
            st.markdown(f"<div style='background:#e0f2fe; padding:10px; border-radius:10px;'>Total Amount: <b>Rs. {total_amt}</b></div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.w_step = 1; st.rerun()
            if c2.button("Next: Payment ➡️"):
                st.session_state.draft_order.update({"shade": sel_shade, "size": sel_size, "qty": sel_qty, "price": u_price, "total": total_amt})
                st.session_state.w_step = 3; st.rerun()

        elif step == 3:
            st.subheader("Select Payment Method")
            pmethod = st.selectbox("Choose One", ["COD (Cash on Delivery)", "JazzCash", "EasyPaisa"])
            st.write("COD select karne par QR display nahi hoga.")
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.w_step = 2; st.rerun()
            if c2.button("Confirm Method ➡️"):
                st.session_state.draft_order['method'] = pmethod
                st.session_state.w_step = 4 if "COD" not in pmethod else 5
                st.rerun()

        elif step == 4:
            st.subheader("Scan QR Code to Pay")
            m_type = st.session_state.draft_order['method']
            qr_to_show = JAZZCASH_QR if m_type == "JazzCash" else EASYPAISA_QR
            
            st.markdown(f"""
                <div class="qr-container">
                    <p>Scan for {m_type} Payment</p>
                    <img src="{qr_to_show}" width="200">
                    <h3 style="color:#1e40af;">Rs. {st.session_state.draft_order['total']}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            st.warning("Payment transfer karke screenshot yahan upload karein.")
            scr = st.file_uploader("Upload Payment Screenshot", type=['jpg','png','jpeg'])
            b64_scr = ""
            if scr: b64_scr = f"data:image/png;base64,{base64.b64encode(scr.read()).decode()}"
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.w_step = 3; st.rerun()
            if c2.button("Review Order 🔍"):
                if not b64_scr: st.error("Screenshot zaroori hai!")
                else: 
                    st.session_state.draft_order['receipt'] = b64_scr
                    st.session_state.w_step = 5; st.rerun()

        elif step == 5:
            st.subheader("Final Order Review")
            d = st.session_state.draft_order
            st.write(f"**Item:** {d['prod']} ({d['size']})")
            st.write(f"**Shade:** {d['shade']} | **Qty:** {d['qty']}")
            st.write(f"**Payable:** Rs. {d['total']} via {d['method']}")
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Change Details"): st.session_state.w_step = 2; st.rerun()
            if c2.button("Submit Order Now ✅", type="primary"):
                with st.spinner("Processing Order..."):
                    inv = generate_invoice_id(orders_db)
                    full_p = f"{d['qty']}x {d['prod']} ({d['size']}) - {d['shade']}"
                    requests.post(SCRIPT_URL, json={
                        "action":"order", "invoice_id":inv, "name":u_name, "phone":u_phone, 
                        "product":full_p, "bill":d['total'], "payment_method":d['method'], "receipt": d.get('receipt','')
                    })
                    st.session_state.wizard_open = False
                    st.session_state.success_popup = True; st.rerun()

    start_wizard()

# --- FINAL SUCCESS POPUP ---
if st.session_state.success_popup:
    @st.dialog("✅ Order Success")
    def show_thanks():
        st.success("Aapka order mehfooz kar liya gaya hai!")
        st.markdown("""
            **Zaroori Note:** Payment wasool hone ka intezar karein. Hamari team confirmation ke liye screenshot check karegi.  
            *Shukriya hamara intekhab karne ka!*
        """)
        if st.button("Close & Back to Dashboard", use_container_width=True):
            st.session_state.success_popup = False
            nav_to("🏠 Dashboard")
    show_thanks()

# ========================================================
# 8. DASHBOARD MODULE (ORIGINAL CARDS)
# ========================================================
if st.session_state.page == "🏠 Dashboard":
    st.markdown(f"## 🏠 Welcome, {u_name}")
    my_ords = orders_db[orders_db['Phone'].apply(normalize_phone) == u_phone]
    total_val = my_ords['Bill'].sum() if not my_ords.empty else 0
    
    st.markdown(f'''
        <div class="card-container">
            <div class="card-blue"><small>ORDERS</small><h3>{len(my_ords)}</h3></div>
            <div class="card-green"><small>TOTAL BILL</small><h3>Rs. {total_val}</h3></div>
            <div class="card-orange"><small>STATUS</small><h3>Active</h3></div>
        </div>
    ''', unsafe_allow_html=True)
    
    st.subheader("🆕 Recent Activity")
    if not my_ords.empty:
        for _, row in my_ords.tail(4).iloc[::-1].iterrows():
            st.markdown(f'''
                <div class="order-row">
                    <div><b>{row["Product"]}</b><br><small>{row["Timestamp"]}</small></div>
                    <div style="text-align:right;"><b>Rs. {row["Bill"]}</b><br><span style="color:#2563eb;">{row["Status"]}</span></div>
                </div>
            ''', unsafe_allow_html=True)
    else: st.info("Koi orders nahi hain.")

# ========================================================
# 9. PROFILE MODULE (PASSWORD CHANGE INCLUDED)
# ========================================================
elif st.session_state.page == "👤 Profile":
    st.header("👤 Personal Profile")
    st.markdown(f'''
        <div class="profile-card">
            <img src="{u_pic}" style="width:150px; height:150px; border-radius:50%; object-fit:cover; border:5px solid #3b82f6;">
            <h2>{u_name}</h2>
            <p>{u_phone}</p>
        </div>
    ''', unsafe_allow_html=True)
    
    # PASSWORD CHANGE SUB-MODULE
    with st.expander("🛠️ Account Settings & Password", expanded=False):
        st.subheader("Change Password")
        curr_pass = st.text_input("Enter Old Password", type="password")
        new_pass = st.text_input("Enter New Password", type="password")
        conf_pass = st.text_input("Confirm New Password", type="password")
        
        if st.button("Update Security Key"):
            if curr_pass != str(u_info['Password']):
                st.error("Purana password ghalat hai!")
            elif new_pass != conf_pass:
                st.error("Passwords match nahi kar rahe!")
            elif len(new_pass) < 4:
                st.error("Password kam az kam 4 huroof ka hona chahiye.")
            else:
                requests.post(SCRIPT_URL, json={"action":"update_password", "phone":u_phone, "password":new_pass})
                st.success("Security Updated! Logout ho raha hai..."); time.sleep(2)
                st.session_state.clear(); st.rerun()
    
    with st.expander("🖼️ Update Profile Picture"):
        new_img = st.file_uploader("Select Image", type=['png','jpg'])
        if new_img and st.button("Apply New Photo"):
            b64 = f"data:image/png;base64,{base64.b64encode(new_img.read()).decode()}"
            requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":u_phone, "photo":b64})
            st.success("Updated!"); time.sleep(1); st.rerun()

# ========================================================
# 10. OTHER MODULES (HISTORY, ADMIN, FEEDBACK)
# ========================================================
elif st.session_state.page == "📜 History":
    st.header("📜 My Order History")
    my_history = orders_df[orders_df['Phone'].apply(normalize_phone) == u_phone]
    st.dataframe(my_history.iloc[::-1], use_container_width=True, hide_index=True)

elif st.session_state.page == "💬 Feedback":
    st.header("💬 Feedback")
    f_text = st.text_area("Hamein batayein hum kaise behtar ho sakte hain?")
    if st.button("Send Review"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":u_phone, "message":f_text})
        st.success("Aapka feedback wasool ho gaya. Shukriya!")

elif st.session_state.page == "🔐 Admin":
    st.header("🛡️ Admin Control Panel")
    t1, t2, t3 = st.tabs(["🛒 Orders", "👥 Users", "📈 Summary"])
    with t1:
        for i, r in orders_db.iloc[::-1].iterrows():
            with st.expander(f"Order #{r['Invoice_ID']} - {r['Name']}"):
                st.write(f"Product: {r['Product']}")
                st.write(f"Payment: {r['Payment_Method']}")
                if 'Receipt' in r and str(r['Receipt']).startswith("data:image"):
                    st.image(r['Receipt'], width=300)
                if st.button("Mark as Complete ✅", key=f"comp_{i}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":r['Invoice_ID']})
                    st.rerun()
    with t2: st.dataframe(users_db)
