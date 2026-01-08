import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import urllib.parse
from fpdf import FPDF
import io
import random

# ================= CONFIGURATION =================
SETTINGS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=1215788411&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJZimOv9kRO-o5Rwftd02VlVzMPhhfRgE_sPQIw_bGra3en-a9Fb491sArBnUv_2H1/exec" 

JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

# --- PDF GENERATOR (With Stamp & ID) ---
def generate_pdf(inv_no, name, phone, items_text, total, pay_method, status, format_type="A4"):
    pdf_size = 'A4' if format_type == "A4" else (80, 210)
    pdf = FPDF(orientation='P', unit='mm', format=pdf_size)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14 if format_type == "A4" else 10)
    pdf.cell(0, 10, "APF PAINT FACTORY", ln=True, align='C')
    pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 7, f"INVOICE NO: {inv_no}", ln=True, align='C')
    pdf.ln(2)
    is_paid = "Paid" in status or "APPROVED" in status
    stamp_txt = "[ PAID / APPROVED ]" if is_paid else "[ PENDING ]"
    r, g, b = (0, 128, 0) if is_paid else (255, 0, 0)
    pdf.set_draw_color(r, g, b); pdf.set_text_color(r, g, b)
    pdf.set_font("Arial", 'B', 14 if format_type == "A4" else 11)
    pdf.cell(0, 12, stamp_txt, border=1, ln=True, align='C')
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 10 if format_type == "A4" else 8)
    pdf.cell(0, 7, f"Customer: {name}", ln=True); pdf.cell(0, 7, f"Phone: {phone}", ln=True)
    pdf.cell(0, 7, f"Method: {pay_method} | Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True)
    pdf.ln(3); pdf.set_font("Arial", 'B', 10 if format_type == "A4" else 8); pdf.cell(0, 7, "Description:", ln=True, border='B')
    pdf.set_font("Arial", size=10 if format_type == "A4" else 8); pdf.multi_cell(0, 7, items_text)
    pdf.ln(5); pdf.set_font("Arial", 'B', 12 if format_type == "A4" else 10); pdf.cell(0, 10, f"TOTAL BILL: Rs. {total}", ln=True, border='T')
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str): pdf_output = pdf_output.encode('latin-1')
    return io.BytesIO(pdf_output)

# --- FINAL CSS STYLING (For Sidebar & All Buttons) ---
st.markdown("""
<style>
    /* Overall Background */
    .stApp { background-color: #f8f9fa !important; }
    
    /* Logout & All Buttons Design */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6, #1e40af) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-weight: bold !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(59, 130, 246, 0.4) !important;
    }

    /* Sidebar Professional Look */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 2px solid #e2e8f0 !important;
    }

    /* Professional Card Structure */
    .apf-card {
        background: white;
        padding: 25px;
        border-radius: 18px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.06);
        border-top: 5px solid #3b82f6;
        text-align: center;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .apf-card:hover { transform: scale(1.02); }
    
    h1, h2, h3 { color: #1e3a8a !important; font-family: 'Inter', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# --- 👤 PROFILE SECTION ---
if menu == "👤 Profile":
    st.markdown(f"<h2 style='text-align:center; padding-bottom:20px;'>Welcome Back, {st.session_state.user_data['Name']}</h2>", unsafe_allow_html=True)
    
    u_p = st.session_state.user_data['Phone'].replace("'","").strip()[-10:]
    u_ords = orders_df[orders_df['Phone'].astype(str).str.contains(u_p, na=False)]
    total_pts = pd.to_numeric(u_ords["Points"], errors="coerce").sum()
    
    # Grid Layout for Cards
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="apf-card">
            <span style="font-size:30px;">📦</span>
            <p style="margin:5px 0; color:#64748b; font-size:14px; font-weight:bold;">TOTAL ORDERS</p>
            <h1 style="margin:0; color:#1e40af;">{len(u_ords)}</h1>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="apf-card">
            <span style="font-size:30px;">⭐</span>
            <p style="margin:5px 0; color:#64748b; font-size:14px; font-weight:bold;">REWARD POINTS</p>
            <h1 style="margin:0; color:#1e40af;">{total_pts:.0f}</h1>
        </div>
        """, unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

@st.cache_data(ttl=5)
def load_data():
    o = pd.read_csv(f"{ORDERS_URL}&cache={datetime.now().timestamp()}", dtype={'Phone': str, 'Invoice_ID': str}).fillna('')
    s = pd.read_csv(f"{SETTINGS_URL}&cache={datetime.now().timestamp()}").fillna('')
    return o, s

orders_df, settings_df = load_data()

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>APF Factory Login</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Login", "📝 Register"])
    with t1:
        ph_in = st.text_input("Mobile No")
        matched = None
        if ph_in:
            # Behtar Matching Line Add kar di gayi hay
            search_num = ph_in.strip()[-10:]
            user_row = orders_df[orders_df['Phone'].astype(str).str.contains(search_num, na=False)]
            if not user_row.empty:
                matched = user_row.iloc[0]
                st.info(f"Welcome Back, {matched['Name']}!")
        
        if st.button("Sign In"):
            if matched is not None:
                if "Approved" in str(matched['Status']):
                    st.session_state.logged_in, st.session_state.user_data = True, matched.to_dict()
                    st.session_state.is_admin = (ph_in.strip().endswith("03005508112"))
                    st.rerun()
                else:
                    st.error("Access Denied: Aapka status 'Approved' nahi hay. Admin se rabta karein.")
            else:
                st.error("Access Denied: Number register nahi hay.")
    with t2:
        r_ph = st.text_input("Register Mobile*")
        r_nm = st.text_input("Full Name*")
        if st.button("Register"):
            if r_nm and r_ph:
                if not orders_df[orders_df['Phone'].astype(str).str.contains(r_ph.strip()[-10:], na=False)].empty:
                    st.error("Already Registered!")
                else:
                    requests.post(SCRIPT_URL, json={"action":"register","name":r_nm,"phone":"'"+r_ph})
                    st.success("Request Sent! Admin ke Approve karne ka intezar karein.")

# --- MAIN DASHBOARD ---
else:
    menu = st.sidebar.radio("Navigation", ["👤 Profile", "🛍️ Shop", "📜 History"] + (["🔐 Admin"] if st.session_state.get('is_admin') else []))
    if st.sidebar.button("Logout"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

    # --- 👤 PROFILE (Updated HTML) ---
    if menu == "👤 Profile":
        st.markdown(f"<h2 style='text-align:center;'>Welcome, {st.session_state.user_data['Name']}</h2>", unsafe_allow_html=True)
        u_p = st.session_state.user_data['Phone'].replace("'","").strip()[-10:]
        u_ords = orders_df[orders_df['Phone'].astype(str).str.contains(u_p, na=False)]
        
        c1, c2 = st.columns(2)
        # Yahan 'stat-card' class ka use lazmi hai design ke liye
        c1.markdown(f'<div class="stat-card"><h3>{len(u_ords)}</h3><p>Orders</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><h3>{pd.to_numeric(u_ords["Points"], errors="coerce").sum():.0f}</h3><p>Points</p></div>', unsafe_allow_html=True)

    # --- 🛍️ SHOP ---
    elif menu == "🛍️ Shop":
        st.header("🛒 Order Items")
        if 'cart' not in st.session_state: st.session_state.cart = []
        scat = st.selectbox("Category", settings_df['Category'].unique())
        sprod = st.selectbox("Product", settings_df[settings_df['Category']==scat]['Product Name'])
        prc = settings_df[settings_df['Product Name']==sprod]['Price'].values[0]
        qty = st.number_input("Qty", 1)
        if st.button("Add to Cart"): st.session_state.cart.append({"Product":sprod,"Qty":qty,"Total":prc*qty}); st.rerun()
        
        if st.session_state.cart:
            total = sum(i['Total'] for i in st.session_state.cart)
            items_str = "\n".join([f"{i['Qty']}x {i['Product']} = {i['Total']}" for i in st.session_state.cart])
            pm = st.radio("Payment", ["COD", "JazzCash", "EasyPaisa"])
            if pm != "COD":
                acc = JAZZCASH_NO if pm == "JazzCash" else EASYPAISA_NO
                st.markdown(f'<div class="pay-box">Pay to: {acc}</div>', unsafe_allow_html=True)
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Mobile:{acc},Amount:{total}")
            
            if st.button(f"Place Order (Rs.{total})"):
                inv_id = f"APF-{random.randint(10000, 99999)}"
                requests.post(SCRIPT_URL, json={"action":"order", "name":st.session_state.user_data['Name'], "phone":"'"+st.session_state.user_data['Phone'], "product":items_str, "bill":float(total), "payment_method":pm, "invoice_id": inv_id})
                st.success(f"Order Successful! ID: {inv_id}")
                pdf = generate_pdf(inv_id, st.session_state.user_data['Name'], st.session_state.user_data['Phone'], items_str, total, pm, "PENDING", "Thermal")
                st.download_button("Download Receipt 📄", pdf.getvalue(), f"Receipt_{inv_id}.pdf")
                st.session_state.cart = []

    # --- 📜 HISTORY ---
    elif menu == "📜 History":
        st.header("Your Orders")
        u_p = st.session_state.user_data['Phone'].replace("'","").strip()[-10:]
        hist = orders_df[orders_df['Phone'].astype(str).str.contains(u_p, na=False)].iloc[::-1]
        search_q = st.text_input("Search by Invoice ID")
        if search_q: hist = hist[hist['Invoice_ID'].astype(str).str.contains(search_q, case=False)]
        
        for _, row in hist.iterrows():
            st.markdown(f'<div class="history-card"><b>ID: {row.get("Invoice_ID", "N/A")}</b><br>{row["Product"]}<br>Rs. {row["Bill"]} | <i>{row["Status"]}</i></div>', unsafe_allow_html=True)

    # --- 🔐 ADMIN ---
    elif menu == "🔐 Admin":
        active = orders_df[orders_df['Status'].astype(str).str.contains("Order", na=False)]
        st.header("Admin Dashboard")
        
        c1, c2 = st.columns(2)
        c1.metric("Pending Orders", len(active))
        c2.metric("Total Sales", f"Rs. {pd.to_numeric(active['Bill'], errors='coerce').sum():,.0f}")
        
        st.markdown("---")
        search_adm = st.text_input("Search Customer Name or ID")
        if search_adm: active = active[active['Name'].str.contains(search_adm, case=False) | active['Invoice_ID'].astype(str).str.contains(search_adm, case=False)]
        
        for idx, row in active.iterrows():
            inv_l = row.get('Invoice_ID', f'ORD_{idx}')
            with st.expander(f"{inv_l} - {row['Name']}"):
                c1, c2, c3 = st.columns(3)
                if c1.button("Paid ✅", key=f"p{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid","phone":row['Phone'],"product":row['Product']})
                    st.rerun()
                if c2.button("Delete 🗑️", key=f"d{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"delete_order","phone":row['Phone'],"product":row['Product']})
                    st.rerun()
                pdf_inv = generate_pdf(inv_l, row['Name'], row['Phone'], row['Product'], row['Bill'], row.get('Payment Method','N/A'), "PAID", "A4")
                c3.download_button("Invoice", pdf_inv.getvalue(), f"INV_{inv_l}.pdf")
