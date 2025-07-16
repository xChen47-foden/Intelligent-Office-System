#!/usr/bin/env python3
"""
Markdown to PDF 转换工具
需要安装依赖：pip install markdown pdfkit
还需要安装 wkhtmltopdf：https://wkhtmltopdf.org/downloads.html
"""

import markdown
import pdfkit
import os
from pathlib import Path

def markdown_to_pdf(md_file, pdf_file=None, css_file=None):
    """
    将 Markdown 文件转换为 PDF
    
    Args:
        md_file: Markdown 文件路径
        pdf_file: 输出的 PDF 文件路径（可选）
        css_file: 自定义 CSS 样式文件（可选）
    """
    # 读取 Markdown 文件
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 转换 Markdown 为 HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables', 'toc']
    )
    
    # HTML 模板
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>智能办公助手 - 软件开发设计文档</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: 24px;
                margin-bottom: 16px;
            }}
            h1 {{
                border-bottom: 2px solid #e1e4e8;
                padding-bottom: 10px;
            }}
            h2 {{
                border-bottom: 1px solid #e1e4e8;
                padding-bottom: 8px;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: Consolas, 'Courier New', monospace;
            }}
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 10px;
                overflow-x: auto;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            table th, table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            table th {{
                background-color: #f4f4f4;
                font-weight: bold;
            }}
            blockquote {{
                border-left: 4px solid #ddd;
                margin: 0;
                padding-left: 20px;
                color: #666;
            }}
            ul, ol {{
                padding-left: 30px;
            }}
            .page-break {{
                page-break-after: always;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # 设置 PDF 选项
    options = {
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-right': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'encoding': "UTF-8",
        'enable-local-file-access': None,
        'no-outline': None
    }
    
    # 如果没有指定输出文件名，使用默认名称
    if not pdf_file:
        pdf_file = Path(md_file).stem + '.pdf'
    
    try:
        # 转换为 PDF
        pdfkit.from_string(html_template, pdf_file, options=options)
        print(f"✅ 成功生成 PDF 文件：{pdf_file}")
        return pdf_file
    except Exception as e:
        print(f"❌ 转换失败：{e}")
        print("请确保已安装 wkhtmltopdf：https://wkhtmltopdf.org/downloads.html")
        return None

def batch_convert(folder_path, output_folder=None):
    """批量转换文件夹中的所有 Markdown 文件"""
    folder = Path(folder_path)
    if not output_folder:
        output_folder = folder / 'pdf_output'
    
    Path(output_folder).mkdir(exist_ok=True)
    
    for md_file in folder.glob('*.md'):
        pdf_name = md_file.stem + '.pdf'
        pdf_path = Path(output_folder) / pdf_name
        markdown_to_pdf(md_file, pdf_path)

if __name__ == '__main__':
    # 转换单个文件
    markdown_to_pdf('智能办公助手_软件开发设计文档.md')
    
    # 如果需要批量转换
    # batch_convert('.') 