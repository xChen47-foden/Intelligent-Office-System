@echo off
chcp 65001 >nul
echo ====================================
echo   Markdown 转 PDF 工具
echo   智能办公助手文档转换器
echo ====================================
echo.

:menu
echo 请选择转换方式：
echo [1] 使用 Python 转换（需要安装 Python）
echo [2] 使用 Node.js 转换（需要安装 Node.js）
echo [3] 使用浏览器打印（最简单）
echo [4] 退出
echo.
set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" goto python_convert
if "%choice%"=="2" goto node_convert
if "%choice%"=="3" goto browser_convert
if "%choice%"=="4" exit
goto menu

:python_convert
echo.
echo 正在检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python
    echo 下载地址：https://www.python.org/downloads/
    pause
    goto menu
)

echo ✅ Python 已安装
echo.
echo 正在安装依赖包...
pip install markdown pdfkit -q

echo.
echo 正在转换文档...
python convert_to_pdf.py
if errorlevel 0 (
    echo.
    echo ✅ 转换成功！
) else (
    echo.
    echo ❌ 转换失败，可能需要安装 wkhtmltopdf
    echo 下载地址：https://wkhtmltopdf.org/downloads.html
)
pause
goto menu

:node_convert
echo.
echo 正在检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Node.js，请先安装 Node.js
    echo 下载地址：https://nodejs.org/
    pause
    goto menu
)

echo ✅ Node.js 已安装
echo.
echo 正在安装依赖包...
call npm install md-to-pdf marked puppeteer

echo.
echo 正在转换文档...
node md2pdf.js
pause
goto menu

:browser_convert
echo.
echo 使用浏览器打印功能：
echo.
echo 1. 我将为您生成一个 HTML 文件
echo 2. 在浏览器中打开该文件
echo 3. 按 Ctrl+P 打印
echo 4. 选择"另存为 PDF"
echo.
echo 正在生成 HTML 文件...

powershell -Command ^
"$md = Get-Content -Path '智能办公助手_软件开发设计文档.md' -Encoding UTF8 -Raw; ^
$html = @'^
<!DOCTYPE html>^
<html>^
<head>^
<meta charset='utf-8'>^
<title>智能办公助手 - 软件开发设计文档</title>^
<style>^
body { font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; max-width: 210mm; margin: 0 auto; padding: 20px; }^
h1, h2, h3 { color: #2c3e50; }^
h1 { border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; }^
h2 { border-bottom: 1px solid #e1e4e8; padding-bottom: 8px; }^
code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }^
pre { background: #f8f8f8; border: 1px solid #ddd; padding: 10px; overflow-x: auto; }^
table { border-collapse: collapse; width: 100%; }^
table th, table td { border: 1px solid #ddd; padding: 8px; }^
table th { background: #f4f4f4; }^
@media print { body { margin: 0; } .page-break { page-break-after: always; } }^
</style>^
<script src='https://cdn.jsdelivr.net/npm/marked/marked.min.js'></script>^
</head>^
<body>^
<div id='content'></div>^
<script>^
document.getElementById('content').innerHTML = marked.parse(`$md`);^
</script>^
</body>^
</html>^
'@; ^
$html | Out-File -FilePath '智能办公助手_软件开发设计文档.html' -Encoding UTF8"

echo.
echo ✅ HTML 文件已生成！
echo.
echo 正在打开浏览器...
start 智能办公助手_软件开发设计文档.html
echo.
echo 请在浏览器中按 Ctrl+P，然后选择"另存为 PDF"
pause
goto menu 