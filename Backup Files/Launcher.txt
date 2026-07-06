# launcher.py (Browser ၁ ကြိမ်ပဲ ပွင့်စေမည့် တိကျသော ဗားရှင်း)
import streamlit.web.cli as stcli
import sys
import os

if __name__ == '__main__':
    # PyInstaller ရဲ့ Internal Path ထဲက app.py တကယ့်ဖိုင်စစ်စစ်တည်နေရာကို ရှာဖွေခြင်း
    if hasattr(sys, '_MEIPASS'):
        script_path = os.path.join(sys._MEIPASS, "app.py")
    else:
        script_path = "app.py"

    # Streamlit အား .exe မဟုတ်သော ၎င်း .py ဖိုင်စစ်စစ်ကို တိုက်ရိုက် မောင်းခိုင်းခြင်း
    sys.argv = ["streamlit", "run", script_path, "--global.developmentMode=false", "--server.port=8501"]
    stcli.main()