import os
import sys
import subprocess

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
        app_path = os.path.join(current_dir, "_internal", "app.py")
        
        # 💡 [ဒီလိုင်းကို ပြင်လိုက်ပါတယ်] Windows Network က တားဆီးခြင်းမရှိစေရန် address နှင့် port ကို အသေ သတ်မှတ်ပေးခြင်း
        cmd = f'streamlit run "{app_path}" --server.headless=false --server.port=8501 --server.address=127.0.0.1 --global.developmentMode=False'
        subprocess.Popen(cmd, shell=True, env=os.environ.copy(), cwd=current_dir)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(current_dir, "dist", "launcher", "_internal", "app.py")
        working_dir = os.path.join(current_dir, "dist", "launcher")
        
        cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless=false", "--server.port=8501", "--server.address=127.0.0.1", "--global.developmentMode=False"]
        subprocess.Popen(cmd, env=os.environ.copy(), cwd=working_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
        sys.exit(0)