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
# STEP 4: NAVIGATION & DASHBOARD (FIXED ICONS)
# ========================================================
else:
    # Navigation menu items (Icons ke sath takay gayib na hon)
    nav_options = ["👤 Profile", "🛍️ New Order", "📜 History"]
    if st.session_state.get('is_admin'):
        nav_options.append("🔐 Admin")
    
    menu = st.sidebar.radio("Navigation", nav_options)
    
    if st.sidebar.button("Logout"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

    if menu == "👤 Profile":
        st.header("Dashboard")
        u_p = st.session_state.user_data['Phone'][-10:]
        u_ords = orders_df[orders_df['Phone'].str.contains(u_p, na=False)]
        points_val = pd.to_numeric(u_ords["Points"], errors="coerce").sum()
        
        # Side-by-Side Cards for Mobile
        st.markdown(f'''
        <div style="display: flex; gap: 10px;">
            <div style="flex: 1; background: white; padding: 15px; border-radius: 12px; text-align: center; border-top: 5px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h2 style="margin:0; color:#1e3a8a;">{len(u_ords)}</h2>
                <p style="margin:0; font-size:14px; color:#64748b;">Orders</p>
            </div>
            <div style="flex: 1; background: white; padding: 15px; border-radius: 12px; text-align: center; border-top: 5px solid #10b981; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h2 style="margin:0; color:#065f46;">{points_val:.0f}</h2>
                <p style="margin:0; font-size:14px; color:#64748b;">Points</p>
            </div>
        </div>
        ''', unsafe_allow_html=True)

# ========================================================
# STEP 5: NEW ORDER (HTML Table & QR Fix)
# ========================================================
    elif menu == "🛍️ New Order":
        st.header("🛒 Create New Order")
        
        # Product Selection
        scat = st.selectbox("Category", settings_df['Category'].unique())
        sprod = st.selectbox("Product", settings_df[settings_df['Category']==scat]['Product Name'])
        prc = float(settings_df[settings_df['Product Name']==sprod]['Price'].values[0])
        
        if 'edit_index' not in st.session_state: st.session_state.edit_index = None
        
        # Quantity Input
        def_qty = 1
        if st.session_state.edit_index is not None:
            def_qty = st.session_state.cart[st.session_state.edit_index]['Qty']
        
        qty = st.number_input("Quantity", min_value=1, value=def_qty, key="qty_input")
        
        btn_txt = "Update Item ✏️" if st.session_state.edit_index is not None else "Add to Cart ➕"
        if st.button(btn_txt):
            if 'cart' not in st.session_state: st.session_state.cart = []
            item_data = {"Product": sprod, "Qty": qty, "Total": prc * qty, "Price": prc}
            if st.session_state.edit_index is not None:
                st.session_state.cart[st.session_state.edit_index] = item_data
                st.session_state.edit_index = None
            else:
                st.session_state.cart.append(item_data)
            st.rerun()

        # --- HTML TABLE REVIEW (Mobile Friendly) ---
        if 'cart' in st.session_state and st.session_state.cart:
            st.markdown("### 📋 Review Items")
            
            table_html = """
            <table style="width:100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; font-size: 14px;">
                <tr style="background: #3b82f6; color: white; text-align: left;">
                    <th style="padding: 10px;">Product</th>
                    <th style="padding: 10px;">Qty</th>
                    <th style="padding: 10px;">Total</th>
                </tr>"""
            
            for idx, item in enumerate(st.session_state.cart):
                table_html += f"""
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 10px;">{item['Product']}</td>
                    <td style="padding: 10px;">{item['Qty']}</td>
                    <td style="padding: 10px;">{item['Total']:.0f}</td>
                </tr>"""
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)

            # Action Buttons (Delete/Edit)
            cols = st.columns(len(st.session_state.cart))
            for i, _ in enumerate(st.session_state.cart):
                with cols[i]:
                    if st.button(f"❌ {i+1}", key=f"del_{i}"):
                        st.session_state.cart.pop(i); st.rerun()
                    if st.button(f"✏️ {i+1}", key=f"ed_{i}"):
                        st.session_state.edit_index = i; st.rerun()

            total_bill = sum(i['Total'] for i in st.session_state.cart)
            st.info(f"**Total Bill: Rs. {total_bill}**")
            
            # --- PAYMENT & FIXED QR ---
            pm = st.radio("Payment Method", ["COD", "JazzCash", "EasyPaisa"])
            if pm != "COD":
                acc = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
                logo = "https://upload.wikimedia.org/wikipedia/commons/b/ba/JazzCash_logo.png" if pm == "JazzCash" else "https://upload.wikimedia.org/wikipedia/commons/f/f2/Easypaisa_logo.png"
                st.markdown(f'<div style="text-align:center; padding:10px; background:white; border-radius:10px;"><img src="{logo}" width="80"><h3>{acc}</h3></div>', unsafe_allow_html=True)
                # Fixed QR URL (Properly encoded)
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-{total_bill}-to-{acc}"
                st.image(qr_url, caption="Scan to Pay", width=150)

            # Confirmation Logic (None Fix)
            inv_str = f"APF-{len(orders_df) + 1:04d}"
            if st.button(f"Confirm Order ({inv_str})"):
                u_name = st.session_state.user_data.get('Name', 'User')
                u_phone = st.session_state.user_data.get('Phone', '000')
                items_str = ", ".join([f"{i['Qty']}x {i['Product']}" for i in st.session_state.cart])
                
                requests.post(SCRIPT_URL, json={
                    "action":"order", "name":u_name, "phone":u_phone, 
                    "product":items_str, "bill":float(total_bill), 
                    "payment_method":pm, "invoice_id": inv_str
                })
                
                # WhatsApp Notification (None Fix)
                msg = f"*New Order*\n*ID:* {inv_str}\n*Bill:* Rs. {total_bill}\n*Customer:* {u_name}"
                wa_url = f"https://wa.me/923005508112?text={requests.utils.quote(msg)}"
                
                st.success(f"Order Success! ID: {inv_str}")
                pdf = generate_pdf(inv_str, u_name, u_phone, items_str, total_bill, pm, "Pending")
                st.download_button("📥 Download Receipt", pdf.getvalue(), f"{inv_str}.pdf")
                st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:12px; border-radius:8px; width:100%; font-weight:bold;">💬 Notify Admin</button></a>', unsafe_allow_html=True)
                st.session_state.cart = []
