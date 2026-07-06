import streamlit as st
import qrcode
import pandas as pd
import base64
import re
import os
import sys
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="MMQR Official 4x6 Bulk Print", layout="centered")
st.title("🖨️ MMQR 4x6 Stand Bulk Printer")

# EXE ထုတ်ထားစဉ် ဖိုင်လမ်းကြောင်းအမှန်ကို ရှာဖွေပေးမည့် လုပ်ဆောင်ချက်
def get_asset_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path

# Local ပုံဖိုင်များကို HTML ထဲတွင် သုံးနိုင်ရန် Base64 ပြောင်းပေးသည့် Function
def load_local_image_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            # 💡 [CRITICAL FIX] Header လုံးဝမပါဘဲ သန့်စင်ပြီးသား Base64 စာသားသက်သက်ကိုသာ ပို့ပေးခြင်း
            return base64.b64encode(image_file.read()).decode()
    return ""

# --- မိမိတို့အသုံးပြုမည့် Official Frame Background ပုံများနှင့် Font ဖိုင်အား လှမ်းဖတ်ခြင်း ---
bg_image_path = get_asset_path("stand_bg.png")
a4_bg_image_path = get_asset_path("a4_stand_bg.png")  # 🚨 [NEW] A4 Composite Frame ပုံလမ်းကြောင်း
font_file_path = get_asset_path("MYANMAR ANGOUN REGULAR.TTF")

FRAME_BACKGROUND = load_local_image_base64(bg_image_path)
A4_FRAME_BACKGROUND = load_local_image_base64(a4_bg_image_path)  # 🚨 [NEW] A4 ပုံအား Base64 သို့ ပြောင်းလဲဖတ်ယူခြင်း

# Custom Font ကို HTML/CSS ထဲတွင် တိုက်ရိုက်သုံးနိုင်ရန် Base64 ပြောင်းခြင်း
FONT_BASE64 = ""
if os.path.exists(font_file_path):
    with open(font_file_path, "rb") as font_file:
        FONT_BASE64 = base64.b64encode(font_file.read()).decode()

# MMQR String ထဲမှ English ဆိုင်အမည် (Tag 59) ကို ဖြတ်ယူပြီး စာလုံးအကြီးပြောင်းမည့် Function
def parse_english_shop_name(qr_string):
    shop_name_en = "MERCHANT SHOP"
    match_en = re.search(r'59(\d{2})', qr_string)
    if match_en:
        length = int(match_en.group(1))
        start_idx = match_en.end()
        shop_name_en = qr_string[start_idx:start_idx+length].upper()
    return shop_name_en

# QR Code Generation Function (High Quality & Exact Box)
def get_qr_base64(qr_string):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=15, 
        border=0,
    )
    qr.add_data(qr_string.strip())
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# --- HTML/CSS ဖြင့် Stand Base Frame ကို ပုံဖော်မည့် Function (Perfect Aspect-Ratio Lock) ---
def build_stand_html(qr_base64, shop_name):
    global FRAME_BACKGROUND
    font_style_injection = ""
    if FONT_BASE64:
        font_style_injection = f"""
        <style>
            @font-face {{
                font-family: 'MyanmarAngoun';
                src: url(data:font/ttf;charset=utf-8;base64,{FONT_BASE64}) format('truetype');
            }}
        </style>
        """
        
    return f"""
    {font_style_injection}
    <div class="mmqr-print-frame" style="width: 384px; height: 576px; position: relative; overflow: hidden; box-sizing: border-box; margin: 0 auto; background: white;">
        <img src="data:image/png;base64,{FRAME_BACKGROUND}" style="position: absolute; top: 0; left: 0; width: 384px; height: 576px; z-index: 1; object-fit: fill; display: block;"/>
        
        <div style="position: absolute; top: 184px; left: 50%; transform: translateX(-50%); width: 215px; height: 215px; background: white; display: flex; align-items: center; justify-content: center; overflow: hidden; z-index: 2;">
            <img src="data:image/png;base64,{qr_base64}" style="width: 98%; height: 98%; object-fit: contain;" />
        </div>
        
        <div style="position: absolute; bottom: 102px; left: 0; right: 0; display: flex; align-items: center; justify-content: center; text-align: center; width: 100%; height: 40px; z-index: 2;">
            <span style="font-family: 'MyanmarAngoun', 'Segoe UI', Arial, sans-serif; font-size: 20px; font-weight: bold; color: #FFB300; letter-spacing: 0.8px; text-transform: uppercase; line-height: 1.2; display: inline-block; width: 90%;">
                {shop_name}
            </span>
        </div>
    </div>
    """

# Session State Index Management
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# ==========================================
# Data Input Methods (Paste text, Google Sheet & Excel File Supported)
# ==========================================
# 💡 Option တွင် Local Excel File အား ရွေးချယ်နိုင်ရန် ထည့်သွင်းထားပါသည်
data_source = st.radio(
    "Select Data Source -", 
    ("Paste Text (Enter Text)", "Google Sheet URL", "Local Excel File (.xlsx)")
)
qr_strings_list = []

# --- ၁။ ရိုးရိုး စာသားရိုက်ထည့်သည့် စနစ် ---
if data_source == "Paste Text (Enter Text)":
    raw_text = st.text_area("QR Strings Paste -", height=150)
    if raw_text:
        qr_strings_list = [line.strip() for line in raw_text.split("\n") if line.strip()]

# --- ၂။ Google Sheet လင့်ခ်ဖြင့် ချိတ်ဆက်သည့် စနစ် ---
elif data_source == "Google Sheet URL":
    sheet_url = st.text_input("Input Google Sheet Share Link :")
    
    if sheet_url:
        if "http" not in sheet_url:
            st.error("⚠️ လက်ရှိထည့်ထားသော စာသားသည် Google Sheet Link မဟုတ်ဘဲ QR စာသား ဖြစ်နေပုံရသည်။ ကျေးဇူးပြု၍ Google Sheet Link အမှန်ကိုသာ ထည့်ပေးပါခင်ဗျာ။")
        else:
            try:
                base_url = sheet_url.split('/edit')[0]
                xlsx_url = f"{base_url}/export?format=xlsx"
                
                xl = pd.ExcelFile(xlsx_url)
                sheet_names = xl.sheet_names
                
                selected_sheet = st.selectbox("Select Tab (Sheet)-", sheet_names)
                df = pd.read_excel(xlsx_url, sheet_name=selected_sheet)
                
                if not df.empty:
                    col_name = st.selectbox("QR String Column ကို ရွေးပါ -", df.columns)
                    if col_name:
                        qr_strings_list = df[col_name].dropna().astype(str).tolist()
                else:
                    st.warning("No Data in your selected sheet. Please check the Google Sheet.")
            except Exception as e:
                st.error(f"Google Sheet reading error - {e}")

# --- ၃။ မိမိစက်ထဲမှ Excel File အား တိုက်ရိုက် တင်သွင်းသည့် စနစ် (NEW) ---
else:
    uploaded_file = st.file_uploader("ကျေးဇူးပြု၍ သင်၏ Excel ဖိုင် (.xlsx) အား ရွေးချယ်ပါ :", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            # တင်လိုက်သော Excel ဖိုင်ထဲရှိ Tab (Sheets) အားလုံးကို ဖတ်ခြင်း
            xl = pd.ExcelFile(uploaded_file)
            sheet_names = xl.sheet_names
            
            # Tab ရွေးချယ်ခိုင်းသည့် Dropdown ပြသခြင်း
            selected_sheet = st.selectbox("Select Tab (Sheet) -", sheet_names)
            
            # ရွေးချယ်လိုက်သော Tab အလိုက် Data ဖတ်ခြင်း
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            
            if not df.empty:
                col_name = st.selectbox("QR String Column ကို ရွေးပါ -", df.columns)
                if col_name:
                    qr_strings_list = df[col_name].dropna().astype(str).tolist()
            else:
                st.warning("ရွေးချယ်ထားသော Excel Tab ထဲတွင် ဒေတာမရှိပါ။")
        except Exception as e:
            st.error(f"Excel ဖိုင်ဖတ်ရာတွင် အမှားအယွင်းရှိနေပါသည် - {e}")
# ==========================================
# --- UI Render & Printing Logic (Speed Optimized) ---
# ==========================================
if qr_strings_list:
    total_data = len(qr_strings_list)
    
    # 💡 Session State ၏ Index အား စစ်ဆေးပြင်ဆင်ခြင်း
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
        
    if st.session_state.current_index >= total_data:
        st.session_state.current_index = 0
    if st.session_state.current_index < 0:
        st.session_state.current_index = 0

    st.markdown("---")
    
    # 🚀 [အမြန်နှုန်းမြှင့်တင်ခြင်း] နံပါတ်တိုက်ရိုက်ရိုက်ထည့်၍ သွားနိုင်သော Box ထည့်သွင်းခြင်း
    # အသုံးပြုသူ မြင်သာစေရန် ကောင်တာကို 1 မှ စတင်ပြသပါမည် (ကုဒ်ထဲတွင်မူ -1 ဖြင့် index ပြန်ချိန်ပါသည်)
    input_page = st.number_input(
        f"🔢 Direct Page Number (1 to {total_data}) :", 
        min_value=1, 
        max_value=total_data, 
        value=int(st.session_state.current_index + 1),
        step=1,
        key="direct_page_input"
    )
    
    # ရိုက်ထည့်လိုက်သော နံပါတ်အတိုင်း Session State ထဲသို့ ချက်ချင်း Sync လုပ်ပေးခြင်း
    st.session_state.current_index = input_page - 1

    # 📊 လက်ရှိရွေးချယ်ထားသော ဆိုင်၏ ဒေတာအား ဖတ်ယူခြင်း
    current_qr_string = qr_strings_list[st.session_state.current_index]
    display_shop_name = parse_english_shop_name(current_qr_string)

    # 📄 စာမျက်နှာအညွှန်းအား ပိုမိုသန့်ရှင်းစွာ ပြသခြင်း
    st.subheader(f"📄 Data information: {st.session_state.current_index + 1} / {total_data}")
        
    try:
        current_qr_base64 = get_qr_base64(current_qr_string)
        
        # iframe ပတ်ဝန်းကျင်သီးသန့်အတွက် Print Style သတ်မှတ်ချက်
        iframe_print_style = """
        <style>
            @page {
                size: 4in 6in;
                margin: 0;
            }
            body {
                margin: 0;
                padding: 0;
                background: white;
            }
            @media print {
                html, body {
                    width: 4in;
                    height: 6in;
                }
                /* 🚨 [PRINT FIX] 4x6 ရိုးရိုးထုတ်ရာတွင်လည်း နောက်ခံ ပုံရိပ်ကို အတင်းအကျပ် ထည့်သွင်းခိုင်းခြင်း */
                img {
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                    display: block !important;
                }
            }
        </style>
        """
        
        # Screen ပေါ်တွင် ပုံမှန်ပြသရန်
        current_stand_html = build_stand_html(current_qr_base64, display_shop_name)
        st.components.v1.html(current_stand_html, height=590)
        
    except Exception as e:
        st.error(f"Code error occurred - {str(e)}")
        
    # ဖိုင်မရှိပါက သတိပေးချက်ပြရန်
    if not FONT_BASE64:
        st.warning("⚠️ 'MYANMAR ANGOUN REGULAR.TTF' not found.")
        
    # ==========================================
    # 🖨️ Paper Size Options & Layout Selection
    # ==========================================
    st.markdown("---")
    st.subheader("🖨️ Print Layout & Paper Options")
    
    paper_option = st.radio(
        "အသုံးပြုမည့် စာရွက်နှင့် ပုံစံကို ရွေးချယ်ပါ :",
        ("4x6 Paper (တစ်ခါလျှင် ၁ ဆိုင်သာ သီးသန့်ထုတ်မည်)", "A4 Paper (တစ်ခါလျှင် ၃ ဆိုင်တွဲ၍ ဒေါင်လိုက်ထုတ်မည်)"),
        key="paper_layout_selection"
    )

    st.markdown("---")
    st.subheader("🧭 Navigation & Preview")

    # --- Navigation Buttons (နံပါတ်တိုက်ရိုက်ရိုက်ခြင်းနှင့် ညှိနှိုင်းထားသည်) ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", use_container_width=True):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1
                st.rerun()
    with col3:
        if st.button("Next ➡️", use_container_width=True):
            if st.session_state.current_index < total_data - 1:
                st.session_state.current_index += 1
                st.rerun()
                
    st.markdown("---")
    st.subheader("🖨️ Printing Process")
    
    print_col1, print_col2 = st.columns(2)
    
    # ==========================================
    # 🖨️ Option ပေါ်မူတည်၍ Frame ပုံစံထုတ်ပေးမည့် Functions (Bug-Free Final Version)
    # ==========================================

    # ၁။ 4x6 မူရင်း Single Frame HTML
    def build_4x6_stand_html(qr_base64, shop_name):
        global FRAME_BACKGROUND
        return f"""
        <div class="mmqr-print-frame" style="width: 384px; height: 576px; position: relative; overflow: hidden; box-sizing: border-box; margin: 0 auto; page-break-after: always; background: white;">
            <img src="data:image/png;base64,{FRAME_BACKGROUND}" style="position: absolute; top: 0; left: 0; width: 384px; height: 576px; z-index: 1; object-fit: fill; display: block;"/>
            <div style="position: absolute; top: 184px; left: 50%; transform: translateX(-50%); width: 215px; height: 215px; background: white; display: flex; align-items: center; justify-content: center; overflow: hidden; z-index: 2;">
                <img src="data:image/png;base64,{qr_base64}" style="width: 98%; height: 98%; object-fit: contain;" />
            </div>
            <div style="position: absolute; bottom: 102px; left: 0; right: 0; display: flex; align-items: center; justify-content: center; text-align: center; width: 100%; height: 40px; z-index: 2;">
                <span style="font-family: 'MyanmarAngoun', 'Segoe UI', Arial, sans-serif; font-size: 20px; font-weight: bold; color: #FFB300; letter-spacing: 0.8px; text-transform: uppercase; line-height: 1.2; display: inline-block; width: 90%;">{shop_name}</span>
            </div>
        </div>
        """

    # ၂။ a4_stand_bg.png ပေါ်တွင် ၃ ဆိုင် ကွက်တိနေရာချမည့် Composite Function
    def build_a4_composite_html(chunk_data):
        global A4_FRAME_BACKGROUND
        clean_a4_bg = str(A4_FRAME_BACKGROUND).replace("\n", "").replace("\r", "").strip() if A4_FRAME_BACKGROUND else ""

        p1_qr, p1_name = (get_qr_base64(chunk_data[0]), parse_english_shop_name(chunk_data[0])) if len(chunk_data) >= 1 else ("", "")
        p2_qr, p2_name = (get_qr_base64(chunk_data[1]), parse_english_shop_name(chunk_data[1])) if len(chunk_data) >= 2 else ("", "")
        l3_qr, l3_name = (get_qr_base64(chunk_data[2]), parse_english_shop_name(chunk_data[2])) if len(chunk_data) >= 3 else ("", "")

        p1_html = f"""
        <div style="position: absolute; top: 0; left: 0; width: 560px; height: 840px; z-index: 2;">
            <div style="position: absolute; top: 360px; left: 130px; width: 300px; height: 300px; display: flex; align-items: center; justify-content: center; overflow: hidden; background: transparent;">
                <img src="data:image/png;base64,{p1_qr}" style="width: 100%; height: 100%; object-fit: contain;"/>
            </div>
            <div style="position: absolute; top: 722px; left: 0; width: 100%; text-align: center;">
                <span style="font-family: 'MyanmarAngoun', sans-serif; font-size: 28px; font-weight: bold; color: #FFB300; text-transform: uppercase; display: inline-block; width: 90%; letter-spacing: 0.8px;">{p1_name}</span>
            </div>
        </div>
        """ if p1_qr else ""

  
        p2_html = f"""
        <div style="position: absolute; top: 0; left: 560px; width: 560px; height: 840px; z-index: 2;">
            <div style="position: absolute; top: 360px; left: 130px; width: 300px; height: 300px; display: flex; align-items: center; justify-content: center; overflow: hidden; background: transparent;">
                <img src="data:image/png;base64,{p2_qr}" style="width: 100%; height: 100%; object-fit: contain;"/>
            </div>
            <div style="position: absolute; top: 722px; left: 0; width: 100%; text-align: center;">
                <span style="font-family: 'MyanmarAngoun', sans-serif; font-size: 28px; font-weight: bold; color: #FFB300; text-transform: uppercase; display: inline-block; width: 90%; letter-spacing: 0.8px;">{p2_name}</span>
            </div>
        </div>
        """ if p2_qr else ""

        
        l3_html = f"""
        <div style="position: absolute; top: 840px; left: 0; width: 1120px; height: 744px; z-index: 2; background: transparent;">
            <div style="position: absolute; top: 225px; left: 410px; width: 300px; height: 300px; display: flex; align-items: center; justify-content: center; overflow: hidden; transform: rotate(90deg); transform-origin: center;">
                <img src="data:image/png;base64,{l3_qr}" style="width: 100%; height: 100%; object-fit: contain;"/>
            </div>
            <div style="position: absolute; top: 0; left: 300px; width: 50px; height: 744px; display: flex; align-items: center; justify-content: center;">
                <span style="font-family: 'MyanmarAngoun', sans-serif; font-size: 28px; font-weight: bold; color: #FFB300; text-transform: uppercase; letter-spacing: 0.8px; transform: rotate(90deg); transform-origin: center; white-space: nowrap; display: inline-block;">
                    {l3_name}
                </span>
            </div>
        </div>
        """ if l3_qr else ""

        return f"""
        <div class="a4-page-box" style="width: 1120px; height: 1584px; position: relative; overflow: hidden; box-sizing: border-box; page-break-after: always; background: white;">
            <img src="data:image/png;base64,{clean_a4_bg}" style="position: absolute; top: 0; left: 0; width: 1120px; height: 1584px; z-index: 1; object-fit: fill; display: block;"/>
            {p1_html}
            {p2_html}
            {l3_html}
        </div>
        """

    # ==========================================
    # 🖨️ Printing Process Layout Engine
    # ==========================================
    print_col1, print_col2 = st.columns(2)
    
    # --- Option 1: Print Current ---
    with print_col1:
        if st.button("🖨️ Print Current", use_container_width=True):
            current_html_content = ""
            
            if "A4" in paper_option:
                start_idx = st.session_state.current_index
                end_idx = min(start_idx + 3, total_data)
                chunk = qr_strings_list[start_idx:end_idx]
                current_html_content = build_a4_composite_html(chunk)
                page_size_css = "A4 portrait"
            else:
                current_html_content = build_4x6_stand_html(current_qr_base64, display_shop_name)
                page_size_css = "4in 6in"

            print_html = f"""
            <html>
            <head>
                {iframe_print_style}
                <style>
                    @font-face {{ font-family: 'MyanmarAngoun'; src: url(data:font/ttf;charset=utf-8;base64,{FONT_BASE64}) format('truetype'); }}
                    @media print {{
                        @page {{ size: {page_size_css}; margin: 0; }}
                        body {{ margin: 0; padding: 0; background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                        img {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; display: block !important; }}
                    }}
                </style>
            </head>
            <body>
                {current_html_content}
                <script>window.onload = function() {{ window.print(); }}</script>
            </body>
            </html>
            """
            st.components.v1.html(print_html, height=0)
            
    # --- Option 2: Print All ---
    with print_col2:
        if st.button("📚 Print All", use_container_width=True):
            all_stands_html = ""
            
            if "A4" in paper_option:
                for i in range(0, total_data, 3):
                    chunk = qr_strings_list[i:i+3]
                    all_stands_html += build_a4_composite_html(chunk)
                page_size_css = "A4 portrait"
            else:
                for qrs in qr_strings_list:
                    s_name = parse_english_shop_name(qrs)
                    q_base = get_qr_base64(qrs)
                    all_stands_html += build_4x6_stand_html(q_base, s_name)
                page_size_css = "4in 6in"

            bulk_print_html = f"""
            <html>
            <head>
                {iframe_print_style}
                <style>
                    @font-face {{ font-family: 'MyanmarAngoun'; src: url(data:font/ttf;charset=utf-8;base64,{FONT_BASE64}) format('truetype'); }}
                    @media print {{
                        @page {{ size: {page_size_css}; margin: 0; }}
                        body {{ margin: 0; padding: 0; background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                        img {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; display: block !important; }}
                    }}
                </style>
            </head>
            <body>
                {all_stands_html}
                <script>
                    window.onload = function() {{
                        setTimeout(function() {{ window.print(); }}, 300);
                    }}
                </script>
            </body>
            </html>
            """
            st.components.v1.html(bulk_print_html, height=0)
            
else:
    st.info("Input Data for view MMQR 4x6 Stand")

