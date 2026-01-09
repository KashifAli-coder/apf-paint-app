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
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxvtcxSnzQ11cCpkEQbb7-wvacH6LYjw7XldVfxORmgFpooxk4UKBsKFYZNueKhTWLe/exec" 
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
# STEP 2: PROFESSIONAL PDF & DATA LOAD (FIXED)
# ========================================================
def generate_pdf(inv_no, name, phone, items_text, total, pay_method, status):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Branded Header (Dark Blue)
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(0, 20, "APF PAINT FACTORY", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, "Official Business Invoice", ln=True, align='C')
    
    # Invoice Details Bar
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  INV NO: {inv_no} | DATE: {datetime.now().strftime('%d-%m-%Y')}", ln=True, fill=True)
    
    # Customer Details
    pdf.ln(5); pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 7, "Customer Name:", 0); pdf.set_font("Arial", '', 10); pdf.cell(0, 7, str(name), ln=True)
    pdf.cell(40, 7, "Phone Number:", 0); pdf.cell(0, 7, str(phone), ln=True)
    pdf.cell(40, 7, "Payment Method:", 0); pdf.cell(0, 7, str(pay_method), ln=True)
    
    # Items Table
    pdf.ln(10); pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(59, 130, 246); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "  ORDER ITEMS DESCRIPTION", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", '', 10); pdf.ln(2)
    pdf.multi_cell(0, 8, str(items_text), border='B')
    
    # Total & Status Stamp
    pdf.ln(5); pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, f"TOTAL BILL: Rs. {total}  ", ln=True, align='R')
    pdf.ln(10); is_paid = "Paid" in str(status) or "APPROVED" in str(status)
    pdf.set_draw_color(0, 150, 0) if is_paid else pdf.set_draw_color(200, 0, 0)
    pdf.set_text_color(0, 150, 0) if is_paid else pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 12, "VERIFIED - PAID" if is_paid else "ORDER PLACED - PENDING", border=1, align='C')
    
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str): pdf_output = pdf_output.encode('latin-1')
    return io.BytesIO(pdf_output)

@st.cache_data(ttl=5)
def load_data():
    try:
        o = pd.read_csv(f"{ORDERS_URL}&cache={datetime.now().timestamp()}", dtype=str).fillna('0')
        s = pd.read_csv(f"{SETTINGS_URL}&cache={datetime.now().timestamp()}", dtype=str).fillna('0')
        return o, s
    except:
        return pd.DataFrame(), pd.DataFrame()

# Yeh line login error (NameError) ko theek karegi
orders_df, settings_df = load_data()

# ========================================================
# STEP 3: LOGIN & REGISTRATION (FIXED)
# ========================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>APF Login</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        ph_input = st.text_input("Mobile No", placeholder="03xxxxxxxxx").strip()
        matched_user = None
        
        # Check if orders_df is loaded properly
        if ph_input and not orders_df.empty:
            search_num = ph_input[-10:]
            # Matching phone in sheet
            user_row = orders_df[orders_df['Phone'].str.contains(search_num, na=False)]
            if not user_row.empty: 
                matched_user = user_row.iloc[0]
        
        if st.button("Sign In"):
            if matched_user is not None:
                u_status = str(matched_user.get('Status', ''))
                if any(x in u_status for x in ["Approved", "Order", "Paid"]):
                    st.session_state.logged_in = True
                    st.session_state.user_data = matched_user.to_dict()
                    st.session_state.is_admin = (ph_input == "03005508112")
                    st.rerun()
                else:
                    st.warning("Account is Pending Approval from Admin.")
            else:
                st.error("Number not found. Please click 'Register' tab below.")
    
    with tab2:
        r_ph = st.text_input("New Mobile No*")
        r_nm = st.text_input("Full Name*")
        if st.button("Request Registration"):
            if r_ph and r_nm:
                requests.post(SCRIPT_URL, json={"action":"register", "name":r_nm, "phone":"'"+r_ph})
                st.success("Request Sent! Admin will approve you soon.")
            else:
                st.warning("Please fill both fields.")

# ========================================================
# STEP 4: USER PROFILE (DASHBOARD)
# ========================================================
else:
    menu = st.sidebar.radio("Navigation", ["👤 Profile", "🛍️ New Order", "📜 History"] + (["🔐 Admin"] if st.session_state.get('is_admin') else []))
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
# STEP 5: NEW ORDER (With WhatsApp Notification & Review)
# ========================================================
    elif menu == "🛍️ New Order":
        st.header("🛒 Create New Order")
        
        # Product Selection
        scat = st.selectbox("Category", settings_df['Category'].unique())
        sprod = st.selectbox("Product", settings_df[settings_df['Category']==scat]['Product Name'])
        prc = float(settings_df[settings_df['Product Name']==sprod]['Price'].values[0])
        qty = st.number_input("Qty", 1)
        
        if st.button("Add to Cart"):
            if 'cart' not in st.session_state: st.session_state.cart = []
            st.session_state.cart.append({"Product":sprod, "Qty":qty, "Total":prc*qty})
            st.rerun()
        
        # Review & Delete Section
        if 'cart' in st.session_state and st.session_state.cart:
            st.markdown("### 📋 Review Your Items")
            for idx, item in enumerate(st.session_state.cart):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{item['Product']}**")
                c2.write(f"{item['Qty']} x {item['Total']/item['Qty']:.0f}")
                if c3.button("❌", key=f"cart_del_{idx}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()
            
            total = sum(i['Total'] for i in st.session_state.cart)
            st.info(f"Total Bill: Rs. {total}")
            
            pm = st.radio("Payment Method", ["COD", "JazzCash", "EasyPaisa"])
            
            # Payment Details (Logos Included)
            if pm != "COD":
                acc_no = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
                logo = "https://upload.wikimedia.org/wikipedia/commons/b/ba/JazzCash_logo.png" if pm == "JazzCash" else "https://upload.wikimedia.org/wikipedia/commons/f/f2/Easypaisa_logo.png"
                st.markdown(f'<div style="text-align:center; background:white; padding:10px; border-radius:10px; border:1px solid #ddd;"><img src="{logo}" width="80"><h3>{acc_no}</h3></div>', unsafe_allow_html=True)

            # Sequential Invoice ID
            inv_id = f"APF-{len(orders_df) + 1:04d}"

            if st.button(f"Confirm Order ({inv_id})"):
                items_str = ", ".join([f"{i['Qty']}x {i['Product']}" for i in st.session_state.cart])
                
                # 1. Send Data to Google Sheet
                requests.post(SCRIPT_URL, json={
                    "action":"order", "name":st.session_state.user_data['Name'], 
                    "phone":st.session_state.user_data['Phone'], "product":items_str, 
                    "bill":float(total), "payment_method":pm, "invoice_id": inv_id
                })
                
                # 2. WHATSAPP NOTIFICATION LOGIC
                # Factory Owner ka number yahan likhein (e.g., 923005508112)
                admin_no = "923005508112" 
                msg = f"*New Order Recieved!*\n*ID:* {inv_id}\n*Customer:* {st.session_state.user_data['Name']}\n*Items:* {items_str}\n*Bill:* Rs. {total}\n*Payment:* {pm}"
                wa_link = f"https://wa.me/{admin_no}?text={requests.utils.quote(msg)}"
                
                st.success(f"Order Placed Successfully! ID: {inv_id}")
                
                # Buttons for PDF and WhatsApp
                col_a, col_b = st.columns(2)
                with col_a:
                    pdf = generate_pdf(inv_id, st.session_state.user_data['Name'], st.session_state.user_data['Phone'], items_str, total, pm, "PENDING")
                    st.download_button("📥 Download Receipt", pdf.getvalue(), f"{inv_id}.pdf")
                with col_b:
                    st.markdown(f' <a href="{wa_link}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:10px; cursor:pointer; width:100%;">💬 WhatsApp Admin</button></a>', unsafe_allow_html=True)
                
                st.session_state.cart = []
