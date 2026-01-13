import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# STEP 1: CONFIGURATION & SETUP
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

st.set_page_config(page_title="Paint Pro Factory Store", layout="wide", initial_sidebar_state="expanded")

# --- ORIGINAL PROFESSIONAL CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: all 0.3s; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    
    /* Dashboard & Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white; padding: 25px; border-radius: 16px; text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-card-green {
        background: linear-gradient(135deg, #065f46, #10b981);
        color: white; padding: 25px; border-radius: 16px; text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-card-orange {
        background: linear-gradient(135deg, #9a3412, #f97316);
        color: white; padding: 25px; border-radius: 16px; text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom Rows */
    .activity-row {
        background: white; padding: 18px; border-radius: 12px; margin-bottom: 12px;
        border: 1px solid #e2e8f0; display: flex; justify-content: space-between;
        align-items: center; transition: 0.2s;
    }
    .activity-row:hover { border-color: #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    
    /* Profile Section */
    .profile-header {
        text-align: center; padding: 30px; background: white; 
        border-radius: 20px; border: 1px solid #e2e8f0; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# STEP 2: CORE FUNCTIONS
# ========================================================
@st.cache_data(ttl=5) # Reduced TTL for faster sync
def load_all_data():
    try:
        t = int(time.time())
        base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
        u = pd.read_csv(base + "Users").fillna('')
        s = pd.read_csv(base + "Settings").fillna('')
        o = pd.read_csv(base + "Orders").fillna('')
        f = pd.read_csv(base + "Feedback").fillna('')
        return u, s, o, f
    except Exception as e:
        st.error(f"Data Connection Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_df, settings_df, orders_df, feedback_df = load_all_data()

def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def get_next_invoice(df):
    try:
        if df.empty or 'Invoice_ID' not in df.columns: return "0001"
        valid_ids = pd.to_numeric(df['Invoice_ID'], errors='coerce').dropna()
        return f"{int(valid_ids.max()) + 1:04d}" if not valid_ids.empty else "0001"
    except: return "0001"

# ========================================================
# STEP 3: SESSION STATE MANAGEMENT
# ========================================================
states = {
    'logged_in': False, 'user_data': {}, 'menu_choice': "🏠 Dashboard",
    'wizard_step': 1, 'temp_order': {}, 'show_wizard': False,
    'cart_items': []
}
for key, val in states.items():
    if key not in st.session_state: st.session_state[key] = val

def set_nav(target):
    st.session_state.menu_choice = target
    st.rerun()

# ========================================================
# STEP 4: AUTHENTICATION (LOGIN / REGISTER)
# ========================================================
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: #1e40af;'>🎨 Paint Factory Store</h1>", unsafe_allow_html=True)
        tab_l, tab_r = st.tabs(["🔐 Secure Login", "📝 New Registration"])
        
        with tab_l:
            l_ph = st.text_input("Registered Phone")
            l_pw = st.text_input("Password", type="password")
            if st.button("Login to Dashboard 🚀", use_container_width=True):
                u_ph = normalize_ph(l_ph)
                match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == l_pw)]
                if not match.empty:
                    row = match.iloc[0]
                    if str(row['Role']).lower() == 'pending':
                        st.warning("Approval Pending. Please contact Admin.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_data = row.to_dict()
                        st.rerun()
                else: st.error("Incorrect details provided.")

        with tab_r:
            r_name = st.text_input("Full Name")
            r_ph = st.text_input("Mobile Number")
            r_pw = st.text_input("Create Password", type="password")
            if st.button("Register Now ✨", use_container_width=True):
                if r_name and r_ph and r_pw:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_ph(r_ph), "password":r_pw})
                    st.success("Registration sent for approval!")
                else: st.error("Please fill all fields.")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR NAVIGATION
# ========================================================
u_data = st.session_state.user_data
u_name = u_data.get('Name', 'User')
u_phone = normalize_ph(u_data.get('Phone', ''))
u_photo = u_data.get('Photo', "https://cdn-icons-png.flaticon.com/512/149/149071.png")

with st.sidebar:
    st.markdown(f'''
        <div style="text-align:center; padding: 20px;">
            <img src="{u_photo}" style="width:110px; height:110px; border-radius:50%; object-fit:cover; border:3px solid #3b82f6;">
            <h3 style="margin-top:10px;">{u_name}</h3>
            <span style="background:#dcfce7; color:#166534; padding:2px 10px; border-radius:15px; font-size:12px;">Verified Member</span>
        </div>
    ''', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🏠 Dashboard", use_container_width=True): set_nav("🏠 Dashboard")
    if st.button("🛍️ Book New Order", use_container_width=True, type="primary"): 
        st.session_state.show_wizard = True
        st.session_state.wizard_step = 1
        st.rerun()
    if st.button("📜 Order History", use_container_width=True): set_nav("📜 History")
    if st.button("👤 My Profile", use_container_width=True): set_nav("👤 Profile")
    if st.button("💬 Send Feedback", use_container_width=True): set_nav("💬 Feedback")
    
    if u_phone == normalize_ph(JAZZCASH_NO):
        st.divider()
        if st.button("🔐 Admin Control", use_container_width=True): set_nav("🔐 Admin")
        
    st.divider()
    if st.button("Logout 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()

# ========================================================
# STEP 6: NEXT/BACK POPUP WIZARD (DETAILED)
# ========================================================
if st.session_state.show_wizard:
    @st.dialog("🛒 Order Booking Wizard")
    def order_wizard_detailed():
        step = st.session_state.wizard_step
        cols_prog = st.columns(4)
        for i in range(4):
            cols_prog[i].markdown(f"**Step {i+1}**" if step == i+1 else f"<span style='color:gray;'>Step {i+1}</span>", unsafe_allow_html=True)
        st.progress(step / 4)

        if step == 1:
            st.subheader("Select Product Type")
            cats = list(settings_df['Category'].unique()) if not settings_df.empty else []
            scat = st.selectbox("Product Category", cats)
            prods = list(settings_df[settings_df['Category'] == scat]['Product Name'].unique()) if scat else []
            sprod = st.selectbox("Specific Product", prods)
            
            if st.button("Continue to Details ➡️", use_container_width=True):
                if sprod:
                    st.session_state.temp_order.update({"cat": scat, "prod": sprod})
                    st.session_state.wizard_step = 2
                    st.rerun()

        elif step == 2:
            st.subheader("Shade & Packing")
            prod_name = st.session_state.temp_order.get('prod')
            p_data = settings_df[settings_df['Product Name'] == prod_name].iloc[0]
            
            colors = [c.split(':')[0] for c in str(p_data['Colors']).split(',') if c.strip()]
            shade = st.selectbox("Select Your Shade", colors)
            
            packs = [p for p in ["20kg", "Gallon", "Quarter"] if float(p_data.get(f"Price_{p}", 0)) > 0]
            size = st.radio("Select Packing Size", packs, horizontal=True)
            qty = st.number_input("Enter Quantity", 1, 1000, 1)
            
            u_price = float(p_data.get(f"Price_{size}", 0))
            st.markdown(f"**Unit Rate:** Rs. {u_price} | **Total:** Rs. {u_price * qty}")
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Change Product"): st.session_state.wizard_step = 1; st.rerun()
            if c2.button("Next: Payment ➡️"):
                st.session_state.temp_order.update({"shade": shade, "size": size, "qty": qty, "price": u_price, "total": u_price * qty})
                st.session_state.wizard_step = 3
                st.rerun()

        elif step == 3:
            st.subheader("Payment Information")
            pmode = st.selectbox("Payment Method", ["Cash on Delivery (COD)", "JazzCash", "EasyPaisa"])
            receipt_b64 = ""
            if "COD" not in pmode:
                st.info(f"Please transfer amount to: {JAZZCASH_NO}")
                up_file = st.file_uploader("Upload Transaction Screenshot", type=['jpg','png','jpeg'])
                if up_file: receipt_b64 = f"data:image/png;base64,{base64.b64encode(up_file.read()).decode()}"
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.wizard_step = 2; st.rerun()
            if c2.button("Review Order 🔍"):
                if "COD" not in pmode and not receipt_b64: st.error("Please upload receipt.")
                else:
                    st.session_state.temp_order.update({"method": pmode, "receipt": receipt_b64})
                    st.session_state.wizard_step = 4
                    st.rerun()

        elif step == 4:
            st.subheader("Final Order Confirmation")
            ord_sum = st.session_state.temp_order
            st.markdown(f"""
                <div style="background:#f1f5f9; padding:15px; border-radius:10px; border-left:4px solid #1e40af;">
                <b>Product:</b> {ord_sum['prod']} ({ord_sum['size']})<br>
                <b>Shade:</b> {ord_sum['shade']}<br>
                <b>Quantity:</b> {ord_sum['qty']}<br>
                <hr>
                <b>Total Bill: Rs. {ord_sum['total']}</b><br>
                <b>Payment:</b> {ord_sum['method']}
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back to Payment"): st.session_state.wizard_step = 3; st.rerun()
            if c2.button("Confirm & Place Order ✅", type="primary"):
                with st.spinner("Processing..."):
                    inv = get_next_invoice(orders_df)
                    p_desc = f"{ord_sum['qty']}x {ord_sum['prod']} ({ord_sum['size']}) Shade: {ord_sum['shade']}"
                    res = requests.post(SCRIPT_URL, json={
                        "action":"order", "invoice_id":inv, "name":u_name, "phone":u_phone, 
                        "product":p_desc, "bill":ord_sum['total'], "payment_method":ord_sum['method'], "receipt": ord_sum['receipt']
                    })
                    if res.status_code == 200:
                        st.session_state.show_wizard = False
                        st.success("Order Placed Successfully!"); time.sleep(1.5); set_nav("🏠 Dashboard")
                    else: st.error("Server Error. Try again.")

    order_wizard_detailed()

# ========================================================
# STEP 7: MAIN MODULES (ORIGINAL DESIGNS)
# ========================================================
menu = st.session_state.menu_choice

if menu == "🏠 Dashboard":
    st.markdown(f"## 🏠 Welcome back, {u_name}")
    u_orders = orders_df[orders_df['Phone'].apply(normalize_ph) == u_phone]
    total_val = u_orders['Bill'].sum() if not u_orders.empty else 0
    
    # ORIGINAL CARDS
    st.markdown(f"""
        <div style="display: flex; gap: 20px; margin-bottom: 30px;">
            <div class="metric-card">
                <small>MY ORDERS</small><br><span style="font-size:32px; font-weight:bold;">{len(u_orders)}</span>
            </div>
            <div class="metric-card-green">
                <small>TOTAL SPENT</small><br><span style="font-size:32px; font-weight:bold;">Rs. {total_val}</span>
            </div>
            <div class="metric-card-orange">
                <small>ACCOUNT</small><br><span style="font-size:24px; font-weight:bold;">ACTIVE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("🆕 Recent Orders")
    if not u_orders.empty:
        for _, r in u_orders.tail(5).iloc[::-1].iterrows():
            st.markdown(f'''
                <div class="activity-row">
                    <div><b>{r["Product"]}</b><br><small>{r["Timestamp"]}</small></div>
                    <div style="text-align:right;"><b>Rs. {r["Bill"]}</b><br><span style="color:#2563eb;">{r["Status"]}</span></div>
                </div>
            ''', unsafe_allow_html=True)
    else: st.info("You haven't placed any orders yet.")

elif menu == "📜 History":
    st.header("📜 My Complete Order History")
    u_orders = orders_df[orders_df['Phone'].apply(normalize_ph) == u_phone]
    if u_orders.empty: st.info("No history found.")
    else:
        st.dataframe(u_orders.iloc[::-1], use_container_width=True, hide_index=True)

elif menu == "👤 Profile":
    st.header("👤 Personal Profile")
    # ORIGINAL CENTERED DESIGN
    st.markdown(f'''
        <div class="profile-header">
            <img src="{u_photo}" style="width:160px; height:160px; border-radius:50%; object-fit:cover; border:5px solid #3b82f6; margin-bottom:15px;">
            <h2>{u_name}</h2>
            <p style="color:gray;">Phone: {u_phone}</p>
        </div>
    ''', unsafe_allow_html=True)
    
    with st.expander("Edit Profile Details"):
        new_photo = st.file_uploader("Upload New Profile Picture", type=['jpg','png'])
        if st.button("Save Changes"):
            if new_photo:
                b64_img = f"data:image/png;base64,{base64.b64encode(new_photo.read()).decode()}"
                requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":u_phone, "photo":b64_img})
                st.success("Profile Updated!"); time.sleep(1); st.rerun()

elif menu == "🔐 Admin":
    st.header("🛡️ Factory Management Panel")
    t1, t2, t3 = st.tabs(["🛒 All Orders", "👥 User Approvals", "📊 Statistics"])
    
    with t1:
        st.subheader("Manage Customer Orders")
        for idx, row in orders_df.iloc[::-1].iterrows():
            with st.expander(f"Order #{row['Invoice_ID']} - {row['Name']}"):
                st.write(f"Items: {row['Product']}")
                st.write(f"Payment: {row['Payment_Method']}")
                if 'Receipt' in row and row['Receipt'] and str(row['Receipt']).startswith("data:image"):
                    st.image(row['Receipt'], width=300)
                if st.button("Mark as Paid & Dispatched ✅", key=f"paid_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                    st.success("Status Updated!"); st.rerun()

    with t2:
        st.subheader("Manage Users")
        st.dataframe(users_df, use_container_width=True)

elif menu == "💬 Feedback":
    st.header("💬 Customer Feedback")
    txt = st.text_area("How was your experience?")
    if st.button("Submit Review"):
        if txt:
            requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":u_phone, "message":txt})
            st.success("Thank you for your feedback!"); time.sleep(1); set_nav("🏠 Dashboard")
