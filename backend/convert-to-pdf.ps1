# PowerShell 脚本：Markdown 转 PDF
# 使用说明：右键以管理员身份运行 PowerShell，然后执行此脚本

param(
    [string]$InputFile = "智能办公助手_软件开发设计文档.md",
    [string]$OutputFile = "智能办公助手_软件开发设计文档.pdf"
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Markdown 转 PDF 工具 (PowerShell)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 检查输入文件是否存在
if (-not (Test-Path $InputFile)) {
    Write-Host "❌ 错误：找不到文件 $InputFile" -ForegroundColor Red
    exit 1
}

# 方法1：使用 Pandoc（如果已安装）
function Convert-WithPandoc {
    $pandocPath = Get-Command pandoc -ErrorAction SilentlyContinue
    if ($pandocPath) {
        Write-Host "✅ 检测到 Pandoc，正在转换..." -ForegroundColor Green
        & pandoc $InputFile -o $OutputFile `
            --pdf-engine=xelatex `
            -V geometry:margin=1in `
            -V mainfont="Microsoft YaHei" `
            -V monofont="Consolas" `
            --highlight-style=tango `
            --toc
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 转换成功！输出文件：$OutputFile" -ForegroundColor Green
            return $true
        }
    }
    return $false
}

# 方法2：生成 HTML 并使用 Edge 浏览器转换
function Convert-WithBrowser {
    Write-Host "正在生成 HTML 文件..." -ForegroundColor Yellow
    
    # 读取 Markdown 内容
    $mdContent = Get-Content -Path $InputFile -Raw -Encoding UTF8
    
    # HTML 模板
    $htmlTemplate = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能办公助手 - 软件开发设计文档</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&display=swap');
        
        body {
            font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
            background: #fff;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: 700;
        }
        
        h1 {
            font-size: 32px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.3em;
        }
        
        h2 {
            font-size: 26px;
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 0.3em;
        }
        
        h3 {
            font-size: 20px;
        }
        
        code {
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: Consolas, 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        pre {
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            line-height: 1.45;
        }
        
        pre code {
            background: none;
            padding: 0;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }
        
        table th, table td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        
        table th {
            background-color: #f6f8fa;
            font-weight: 700;
        }
        
        table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            margin: 0;
            padding-left: 20px;
            color: #666;
            font-style: italic;
        }
        
        ul, ol {
            padding-left: 30px;
            margin: 1em 0;
        }
        
        li {
            margin: 0.5em 0;
        }
        
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        .page-break {
            page-break-after: always;
        }
        
        @media print {
            body {
                margin: 0;
                padding: 15mm;
            }
            
            h1, h2, h3 {
                page-break-after: avoid;
            }
            
            pre, table, blockquote {
                page-break-inside: avoid;
            }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
    <div id="content"></div>
    <script>
        // Markdown 内容
        const mdContent = `$($mdContent.Replace('`', '\`').Replace('$', '\$'))`;
        
        // 配置 marked
        marked.setOptions({
            breaks: true,
            gfm: true,
            tables: true,
            smartLists: true,
            smartypants: true
        });
        
        // 渲染 Markdown
        document.getElementById('content').innerHTML = marked.parse(mdContent);
    </script>
</body>
</html>
"@
    
    # 保存 HTML 文件
    $htmlFile = $InputFile -replace '\.md$', '.html'
    $htmlTemplate | Out-File -FilePath $htmlFile -Encoding UTF8
    
    Write-Host "✅ HTML 文件已生成：$htmlFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "请按以下步骤操作：" -ForegroundColor Yellow
    Write-Host "1. 浏览器将自动打开生成的 HTML 文件"
    Write-Host "2. 按 Ctrl+P 打开打印对话框"
    Write-Host "3. 选择 '另存为 PDF' 或 'Microsoft Print to PDF'"
    Write-Host "4. 保存文件为：$OutputFile"
    Write-Host ""
    
    # 打开浏览器
    Start-Process $htmlFile
    
    return $true
}

# 主程序
Write-Host "开始转换 $InputFile ..." -ForegroundColor Yellow
Write-Host ""

# 尝试使用 Pandoc
if (-not (Convert-WithPandoc)) {
    Write-Host "未检测到 Pandoc，使用浏览器方法..." -ForegroundColor Yellow
    Convert-WithBrowser
}

Write-Host ""
Write-Host "转换完成！" -ForegroundColor Green
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 