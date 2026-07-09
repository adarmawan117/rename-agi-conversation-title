@echo off
echo Membangun AGI Renamer...
.\.venv\Scripts\pyinstaller.exe --onefile --noconsole --icon="google-antigravity.ico" --add-data="google-antigravity.ico;." --name "AGI Renamer" main_gui.py
echo Selesai!
