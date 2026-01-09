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
# STEP 4: NAVIGATION
# ========================================================
else:
    nav_options = ["👤 Profile", "🛍️ Shop", "📜 History"]
    if st.session_state.get('is_admin'):
        nav_options.append("🔐 Admin")
    
    menu = st.sidebar.radio("Navigation", nav_options)
    
    if st.sidebar.button("Logout"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ========================================================
# STEP 5: SHOP (INTERACTIVE TABLE - NO BUTTONS)
# ========================================================
    if menu == "🛍️ Shop":
        st.header("🛒 Order Menu")
        
        # Selection
        scat = st.selectbox("Category", settings_df['Category'].unique())
        sprod = st.selectbox("Product", settings_df[settings_df['Category']==scat]['Product Name'])
        prc = float(settings_df[settings_df['Product Name']==sprod]['Price'].values[0])
        qty = st.number_input("Enter Quantity", min_value=1, value=1)
        
        if st.button("Add to Cart ➕"):
            if 'cart_df' not in st.session_state:
                st.session_state.cart_df = pd.DataFrame(columns=["Product", "Qty", "Price", "Total"])
            
            new_item = pd.DataFrame([{"Product": sprod, "Qty": qty, "Price": prc, "Total": prc * qty}])
            st.session_state.cart_df = pd.concat([st.session_state.cart_df, new_item], ignore_index=True)
            st.rerun()

        # --- THE INTERACTIVE TABLE (Solves your Delete/Edit issue) ---
        if 'cart_df' in st.session_state and not st.session_state.cart_df.empty:
            st.subheader("📋 Review Your Items")
            st.info("💡 Tip: Click on Qty to change it. Select a row and press 'Delete' on your keyboard or use the trash icon to remove.")
            
            # This editor handles everything inside the table
            edited_df = st.data_editor(
                st.session_state.cart_df,
                column_config={
                    "Product": st.column_config.TextColumn("Product", disabled=True),
                    "Qty": st.column_config.NumberColumn("Qty", min_value=1, step=1, format="%d"),
                    "Price": st.column_config.NumberColumn("Price", disabled=True, format="Rs %d"),
                    "Total": st.column_config.NumberColumn("Total", disabled=True, format="Rs %d"),
                },
                num_rows="dynamic", # Enables the trash icon for deleting rows
                use_container_width=True,
                key="cart_editor"
            )
            
            # Re-calculate Total Bill
            edited_df["Total"] = edited_df["Qty"] * edited_df["Price"]
            st.session_state.cart_df = edited_df
            total_bill = edited_df["Total"].sum()
            
            st.markdown(f"### **Grand Total: Rs. {total_bill:.0f}**")
            
            # Payment
            pm = st.radio("Payment Method", ["COD", "JazzCash", "EasyPaisa"])
            if pm != "COD":
                acc = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
                st.warning(f"Transfer Rs. {total_bill:.0f} to {pm}: {acc}")
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Pay-{total_bill}-to-{acc}", width=150)

            # Confirm Order
            inv_id = f"APF-{len(orders_df) + 1:04d}"
            if st.button(f"Confirm Order ({inv_id})"):
                u_name = st.session_state.user_data.get('Name', 'User')
                u_phone = st.session_state.user_data.get('Phone', '000')
                items_text = ", ".join([f"{int(r['Qty'])}x {r['Product']}" for _, r in edited_df.iterrows()])
                
                # Send to Sheets
                requests.post(SCRIPT_URL, json={
                    "action":"order", "name":u_name, "phone":u_phone, 
                    "product":items_text, "bill":float(total_bill), 
                    "payment_method":pm, "invoice_id": inv_id
                })
                
                # WhatsApp & PDF
                wa_msg = f"*New Order*\n*ID:* {inv_id}\n*Customer:* {u_name}\n*Total:* Rs. {total_bill}"
                wa_url = f"https://wa.me/923005508112?text={requests.utils.quote(wa_msg)}"
                
                st.success(f"Order Placed! ID: {inv_id}")
                pdf = generate_pdf(inv_id, u_name, u_phone, items_text, total_bill, pm, "Pending")
                st.download_button("📥 Download Receipt", pdf.getvalue(), f"{inv_id}.pdf")
                st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:12px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer;">💬 Notify Admin (WhatsApp)</button></a>', unsafe_allow_html=True)
                
                st.session_state.cart_df = pd.DataFrame(columns=["Product", "Qty", "Price", "Total"])
                st.rerun()

    elif menu == "👤 Profile":
        st.header("User Dashboard")
        # (Profile logic stays same)

    elif menu == "🔐 Admin":
        st.header("Admin Control")
        # Fixed Admin Logic (No white screen)
        pending = orders_df[orders_df['Status'].str.contains("Order|Pending", na=False)]
        if pending.empty:
            st.info("No pending orders.")
        else:
            for idx, row in pending.iterrows():
                with st.expander(f"Order: {row.get('Invoice_ID', 'N/A')} - {row['Name']}"):
                    st.write(f"**Items:** {row['Product']}")
                    st.write(f"**Bill:** Rs. {row['Bill']}")
                    if st.button("Mark Paid ✅", key=f"paid_{idx}"):
                        requests.post(SCRIPT_URL, json={"action":"mark_paid","phone":row['Phone'],"product":row['Product']})
                        st.rerun()
