@echo off

setlocal enabledelayedexpansion

:: ========================
:: 1. 切换到指定目录
:: ========================
set "TARGET_DIR=C:\Users\52483\Desktop\xml"
if not exist "%TARGET_DIR%" (
    echo 错误：目录 %TARGET_DIR% 不存在！
    pause
    exit /b 1
)
cd /d "%TARGET_DIR%"
echo 已切换至：%cd%

:: ========================
:: 2. 30秒倒计时准备，用户选择
:: ========================
echo.
echo 准备阶段 - 30秒倒计时...
echo 请确认以下程序将被关闭：
echo   - Edge浏览器
echo.
echo 选择：
echo   [1] 立即运行
echo   [2] 退出运行
echo.
echo (30秒后无操作将自动继续运行)
echo.

choice /c 12 /n /t 30 /d 1 /m "请选择操作"
if errorlevel 2 (
    echo 用户选择退出运行。
    exit /b 0
)
echo 继续执行...

:: ========================
:: 3. 关闭 Edge 浏览器
:: ========================
echo 正在关闭 Edge 浏览器...
taskkill /f /im msedge.exe >nul 2>&1
if errorlevel 1 (
    echo 未发现正在运行的 Edge 进程或关闭失败。
) else (
    echo Edge 浏览器已关闭。
)

:: ========================
:: 4. 删除当前目录下的所有 XML 文件
:: ========================
echo 正在删除旧的 XML 文件...
del /q "*.xml" 2>nul
echo 已删除所有 XML 文件。

:: ========================
:: 5. 执行下载操作（Python 脚本）
:: ========================
echo 正在执行下载脚本 pyautogui_download_optimized.py ...
if not exist "pyautogui_download_optimized.py" (
    echo 错误：未找到 pyautogui_download_optimized.py 文件！
    pause
    exit /b 1
)
python pyautogui_download_optimized.py
if errorlevel 1 (
    echo 下载脚本执行出错，请检查。
    pause
    exit /b 1
)
echo 下载完成。

:: ========================
:: 6. 生成时间戳并创建文件夹，复制 XML 文件，然后移动到 HisData
:: ========================
echo 正在生成时间戳...

:: 获取当前日期时间（兼容中英文系统）
for /f "tokens=2 delims==" %%I in ('wmic OS Get localdatetime /value 2^>nul') do set datetime=%%I
if "%datetime%"=="" (
    :: 备用方案：使用 %date% 和 %time%
    set "year=%date:~0,4%"
    set "month=%date:~5,2%"
    set "day=%date:~8,2%"
    set "hour=%time:~0,2%"
    set "minute=%time:~3,2%"
    set "second=%time:~6,2%"
    if "!hour:~0,1!"==" " set "hour=0!hour:~1,1!"
) else (
    set "year=%datetime:~0,4%"
    set "month=%datetime:~4,2%"
    set "day=%datetime:~6,2%"
    set "hour=%datetime:~8,2%"
    set "minute=%datetime:~10,2%"
    set "second=%datetime:~12,2%"
)
set "timestamp=%year%%month%%day%_%hour%%minute%%second%"
echo 时间戳：%timestamp%

:: 创建时间戳文件夹
set "BACKUP_DIR=%TARGET_DIR%\%timestamp%"
mkdir "%BACKUP_DIR%" 2>nul

:: 复制所有 XML 文件到时间戳文件夹
echo 正在备份 XML 文件到 %timestamp% 文件夹...
copy "*.xml" "%BACKUP_DIR%\" >nul
if errorlevel 1 (
    echo 警告：未找到 XML 文件或复制失败。
) else (
    echo 已复制所有 XML 文件。
)

:: 确保目标 HisData 目录存在
set "HISDATA_DIR=%TARGET_DIR%\HisData"
if not exist "%HISDATA_DIR%" mkdir "%HISDATA_DIR%"

:: 移动时间戳文件夹到 HisData 目录
echo 正在移动 %timestamp% 到 HisData 目录...
move "%BACKUP_DIR%" "%HISDATA_DIR%\" >nul
if errorlevel 1 (
    echo 移动失败，请检查权限或路径。
    pause
    exit /b 1
)
echo 已移动至 %HISDATA_DIR%\%timestamp%

:: ========================
:: 7. 运行python应用
:: ========================
echo 正在启动 python 应用 (a.py) ...
if not exist "a.py" (
    echo 错误：未找到 a.py 文件！
    pause
    exit /b 1
)
python a.py

echo 正在解析 XML 生成 his_data.js...
python parse_xml.py
if errorlevel 1 pause & exit /b
echo 刷新完成！

:: 脚本结束
pause