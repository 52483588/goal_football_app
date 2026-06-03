@echo off

cd /d "%~dp0"
echo 正在解析 XML 生成 his_data.js...
python parse_xml.py
if errorlevel 1 pause & exit /b
echo 正在生成 index.html...
python build_html.py
if errorlevel 1 pause & exit /b
echo 刷新完成！
pause
