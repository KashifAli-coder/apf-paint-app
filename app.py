# ========================================================
# STEP 1: CONFIGURATION & STYLING
# ========================================================
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from fpdf import FPDF
import io
import random

# Google Sheets & Payment Info
SETTINGS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=1215788411&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJZimOv9kRO-o5Rwftd02VlVzMPhhfRgE_sPQIw_bGra3en-a9Fb491sArBnUv_2H1/exec" 
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

st.set_page_config(page_title="APF Factory", layout="centered")
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa !important; }
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6, #1e40af) !important;
        color: white !important; border-radius: 12px !important; border: none !important;
        padding: 0.5rem 1rem !important; font-weight: bold !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 2px solid #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ========================================================
# STEP 2: FUNCTIONS (PDF & DATA LOAD)
# ========================================================
def generate_pdf(inv_no, name, phone, items_text, total, pay_method, status, format_type="A4"):
    pdf = FPDF(orientation='P', unit='mm', format='A4' if format_type == "A4" else (80, 210))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "APF PAINT FACTORY", ln=True, align='C')
    pdf.set_text_color(59, 130, 246); pdf.cell(0, 7, f"INV: {inv_no}", ln=True, align='C')
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", size=10)
    pdf.cell(0, 7, f"Customer: {name}", ln=True); pdf.cell(0, 7, f"Total: Rs. {total}", ln=True)
    pdf.ln(5); pdf.multi_cell(0, 7, f"Items:\n{items_text}")
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str): pdf_output = pdf_output.encode('latin-1')
    return io.BytesIO(pdf_output)

@st.cache_data(ttl=5)
def load_data():
    o = pd.read_csv(f"{ORDERS_URL}&cache={datetime.now().timestamp()}", dtype=str).fillna('0')
    s = pd.read_csv(f"{SETTINGS_URL}&cache={datetime.now().timestamp()}", dtype=str).fillna('0')
    return o, s

orders_df, settings_df = load_data()

# ========================================================
# STEP 3: LOGIN & REGISTRATION
# ========================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>APF Login</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Login", "📝 Register"])
    with t1:
        ph_in = st.text_input("Mobile No").strip()
        matched = None
        if ph_in:
            search_num = ph_in[-10:]
            user_row = orders_df[orders_df['Phone'].str.contains(search_num, na=False)]
            if not user_row.empty: matched = user_row.iloc[0]
        if st.button("Sign In"):
            if matched is not None and "Approved" in str(matched['Status']):
                st.session_state.logged_in, st.session_state.user_data = True, matched.to_dict()
                st.session_state.is_admin = (ph_in.endswith("03005508112"))
                st.rerun()
            else: st.error("Access Denied: Pending Approval or Not Found.")
    with t2:
        r_ph, r_nm = st.text_input("Mobile*"), st.text_input("Name*")
        if st.button("Register"):
            requests.post(SCRIPT_URL, json={"action":"register","name":r_nm,"phone":"'"+r_ph})
            st.success("Registration Request Sent!")

# ========================================================
# STEP 4: USER PROFILE (DASHBOARD)
# ========================================================
else:
    menu = st.sidebar.radio("Navigation", ["👤 Profile", "🛍️ Shop", "📜 History"] + (["🔐 Admin"] if st.session_state.get('is_admin') else []))
    if st.sidebar.button("Logout"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

    if menu == "👤 Profile":
        st.markdown(f"<h2 style='text-align:center;'>Dashboard</h2>", unsafe_allow_html=True)
        u_p = st.session_state.user_data['Phone'][-10:]
        u_ords = orders_df[orders_df['Phone'].str.contains(u_p, na=False)]
        points_val = pd.to_numeric(u_ords["Points"], errors="coerce").sum()
        
        st.markdown(f"""
        <div style="display: flex; gap: 10px; justify-content: center; width: 100%;">
            <div style="flex: 1; background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 5px solid #3b82f6; text-align: center;">
                <div style="font-size: 30px;">📦</div><p style="font-size: 11px; font-weight: bold; margin: 5px 0;">ORDERS</p><h2>{len(u_ords)}</h2>
            </div>
            <div style="flex: 1; background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 5px solid #10b981; text-align: center;">
                <div style="font-size: 30px;">⭐</div><p style="font-size: 11px; font-weight: bold; margin: 5px 0;">POINTS</p><h2>{points_val:.0f}</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ========================================================
# STEP 5: SHOP, HISTORY & ADMIN
# ========================================================
    elif menu == "🛍️ Shop":
        scat = st.selectbox("Category", settings_df['Category'].unique())
        sprod = st.selectbox("Product", settings_df[settings_df['Category']==scat]['Product Name'])
        prc = float(settings_df[settings_df['Product Name']==sprod]['Price'].values[0])
        qty = st.number_input("Qty", 1)
        if st.button("Add to Cart"):
            if 'cart' not in st.session_state: st.session_state.cart = []
            st.session_state.cart.append({"Product":sprod, "Qty":qty, "Total":prc*qty})
            st.rerun()
        
        if 'cart' in st.session_state and st.session_state.cart:
            total = sum(i['Total'] for i in st.session_state.cart)
            items_str = "\n".join([f"{i['Qty']}x {i['Product']}" for i in st.session_state.cart])
            st.info(f"Total Bill: Rs. {total}")
            pm = st.radio("Payment", ["COD", "JazzCash", "EasyPaisa"])
            if pm != "COD":
                acc = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-to-{acc}-Amount-{total}")
            if st.button("Confirm Order"):
                requests.post(SCRIPT_URL, json={"action":"order", "name":st.session_state.user_data['Name'], "phone":"'"+st.session_state.user_data['Phone'], "product":items_str, "bill":float(total), "payment_method":pm, "invoice_id": f"APF-{random.randint(10000,99999)}"})
                st.session_state.cart = []
                st.success("Order Placed Successfully!")

    elif menu == "📜 History":
        u_p = st.session_state.user_data['Phone'][-10:]
        hist = orders_df[orders_df['Phone'].str.contains(u_p, na=False)].iloc[::-1]
        for _, row in hist.iterrows():
            st.markdown(f'<div style="background:white; padding:15px; border-radius:10px; margin-bottom:10px; border-left:5px solid #3b82f6;"><b>ID: {row.get("Invoice_ID", "N/A")}</b><br>{row["Product"]}<br><b>Rs. {row["Bill"]}</b></div>', unsafe_allow_html=True)

    elif menu == "🔐 Admin":
        active = orders_df[orders_df['Status'].str.contains("Order", na=False)]
        st.header("Admin Control")
        for idx, row in active.iterrows():
            with st.expander(f"{row['Name']} - {row.get('Invoice_ID', 'N/A')}"):
                c1, c2 = st.columns(2)
                if c1.button("Paid ✅", key=f"paid_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid","phone":row['Phone'],"product":row['Product']})
                    st.rerun()
                if c2.button("Delete 🗑️", key=f"del_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"delete_order","phone":row['Phone'],"product":row['Product']})
                    st.rerun()
