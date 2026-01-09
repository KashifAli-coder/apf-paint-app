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
# STEP 5: NEW ORDER (SHOP) - COMPLETE WITH ALL FEATURES
# ========================================================
    elif menu == "🛍️ New Order":
        st.header("🛒 Create New Order")
        
        # Product Selection Area
        scat = st.selectbox("Category", settings_df['Category'].unique())
        sprod = st.selectbox("Product", settings_df[settings_df['Category']==scat]['Product Name'])
        prc = float(settings_df[settings_df['Product Name']==sprod]['Price'].values[0])
        qty = st.number_input("Enter Quantity", 1)
        
        if st.button("Add to Cart"):
            if 'cart' not in st.session_state: st.session_state.cart = []
            st.session_state.cart.append({"Product":sprod, "Qty":qty, "Total":prc*qty})
            st.rerun()
        
        # --- CART REVIEW & DELETE OPTION ---
        if 'cart' in st.session_state and st.session_state.cart:
            st.markdown("---")
            st.subheader("📋 Review Your Order")
            for idx, item in enumerate(st.session_state.cart):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{item['Product']}**")
                c2.write(f"{item['Qty']}x (Rs.{item['Total']/item['Qty']:.0f})")
                if c3.button("❌", key=f"del_{idx}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()
            
            total_bill = sum(i['Total'] for i in st.session_state.cart)
            st.success(f"Total Bill: Rs. {total_bill}")
            
            # --- PAYMENT WITH LOGOS ---
            pm = st.radio("Select Payment Method", ["COD", "JazzCash", "EasyPaisa"])
            if pm != "COD":
                acc = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
                logo = "https://upload.wikimedia.org/wikipedia/commons/b/ba/JazzCash_logo.png" if pm == "JazzCash" else "https://upload.wikimedia.org/wikipedia/commons/f/f2/Easypaisa_logo.png"
                st.markdown(f'''
                <div style="background: white; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; margin-bottom: 10px;">
                    <img src="{logo}" width="100">
                    <h3 style="margin: 5px 0; color: #1e3a8a;">{acc}</h3>
                    <p style="font-size: 11px; color: #64748b;">Transfer <b>Rs. {total_bill}</b> then click confirm</p>
                </div>
                ''', unsafe_allow_html=True)
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-to-{acc}-Amount-{total_bill}", caption="Scan to Pay")

            # --- SEQUENTIAL INVOICE & CONFIRMATION ---
            inv_str = f"APF-{len(orders_df) + 1:04d}" 

            if st.button(f"Confirm Order ({inv_str})"):
                items_str = ", ".join([f"{i['Qty']}x {i['Product']}" for i in st.session_state.cart])
                
                # Send to Sheet
                requests.post(SCRIPT_URL, json={
                    "action":"order", "name":st.session_state.user_data['Name'], 
                    "phone":st.session_state.user_data['Phone'], "product":items_str, 
                    "bill":float(total_bill), "payment_method":pm, "invoice_id": inv_str
                })
                
                # WhatsApp Link Logic
                admin_msg = f"*New Order Recieved!*\n*ID:* {inv_str}\n*Customer:* {st.session_state.user_data['Name']}\n*Items:* {items_str}\n*Total:* Rs. {total_bill}\n*Payment:* {pm}"
                wa_url = f"https://wa.me/923005508112?text={requests.utils.quote(admin_msg)}"
                
                # PDF Generation
                pdf = generate_pdf(inv_str, st.session_state.user_data['Name'], st.session_state.user_data['Phone'], items_str, total_bill, pm, "Pending")
                
                st.success(f"Order Success! ID: {inv_str}")
                
                col_pdf, col_wa = st.columns(2)
                with col_pdf:
                    st.download_button("📥 Download Receipt", pdf.getvalue(), f"{inv_str}.pdf")
                with col_wa:
                    st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:8px; width:100%; cursor:pointer; font-weight:bold;">💬 Notify Admin</button></a>', unsafe_allow_html=True)
                
                st.session_state.cart = []

    elif menu == "📜 History":
        st.header("Order History")
        u_p = st.session_state.user_data['Phone'][-10:]
        hist = orders_df[orders_df['Phone'].str.contains(u_p, na=False)].iloc[::-1]
        for _, row in hist.iterrows():
            st.markdown(f'''
            <div style="background:white; padding:15px; border-radius:10px; margin-bottom:10px; border-left:5px solid #3b82f6; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                <b style="color:#1e3a8a;">ID: {row.get("Invoice_ID", "N/A")}</b><br>
                <span style="font-size:14px;">{row["Product"]}</span><br>
                <b style="color:#10b981;">Rs. {row["Bill"]}</b>
            </div>
            ''', unsafe_allow_html=True)

    elif menu == "🔐 Admin":
        st.header("Admin Control Panel")
        active = orders_df[orders_df['Status'].str.contains("Order", na=False)]
        for idx, row in active.iterrows():
            inv_l = row.get('Invoice_ID', f'ORD-{idx}')
            with st.expander(f"👤 {row['Name']} - {inv_l}"):
                c1, c2, c3 = st.columns(3)
                if c1.button("Paid ✅", key=f"adm_p_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid","phone":row['Phone'],"product":row['Product'],"bill":row['Bill']})
                    st.rerun()
                if c2.button("Delete 🗑️", key=f"adm_d_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"delete_order","phone":row['Phone'],"product":row['Product']})
                    st.rerun()
                adm_pdf = generate_pdf(inv_l, row['Name'], row['Phone'], row['Product'], row['Bill'], "N/A", "PAID")
                c3.download_button("📄 PDF", adm_pdf.getvalue(), f"Inv_{inv_l}.pdf", key=f"pdf_{idx}")
