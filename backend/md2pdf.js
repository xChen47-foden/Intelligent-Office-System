#!/usr/bin/env node
/**
 * Markdown to PDF 转换工具 (Node.js版本)
 * 需要安装依赖：npm install md-to-pdf marked puppeteer
 */

const { mdToPdf } = require('md-to-pdf');
const fs = require('fs').promises;
const path = require('path');

// PDF 样式配置
const pdfConfig = {
    stylesheet: `
        body {
            font-family: -apple-system, 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        h1 {
            font-size: 28px;
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 10px;
        }
        h2 {
            font-size: 24px;
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 8px;
        }
        h3 {
            font-size: 20px;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: Consolas, monospace;
        }
        pre {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 10px;
            overflow-x: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        table th, table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        table th {
            background-color: #f4f4f4;
            font-weight: bold;
        }
        blockquote {
            border-left: 4px solid #ddd;
            margin: 0;
            padding-left: 20px;
            color: #666;
        }
        @media print {
            .page-break {
                page-break-after: always;
            }
        }
    `,
    pdf_options: {
        format: 'A4',
        margin: {
            top: '20mm',
            right: '20mm',
            bottom: '20mm',
            left: '20mm'
        },
        printBackground: true,
        displayHeaderFooter: true,
        headerTemplate: `
            <div style="font-size: 10px; text-align: center; width: 100%;">
                智能办公助手 - 软件开发设计文档
            </div>
        `,
        footerTemplate: `
            <div style="font-size: 10px; text-align: center; width: 100%;">
                第 <span class="pageNumber"></span> 页 / 共 <span class="totalPages"></span> 页
            </div>
        `
    }
};

async function convertMdToPdf(inputFile, outputFile) {
    try {
        console.log(`📄 正在读取文件: ${inputFile}`);
        
        // 检查文件是否存在
        await fs.access(inputFile);
        
        // 转换
        console.log('🔄 正在转换为 PDF...');
        const pdf = await mdToPdf({ path: inputFile }, pdfConfig);
        
        if (pdf) {
            // 保存 PDF
            const outputPath = outputFile || inputFile.replace('.md', '.pdf');
            await fs.writeFile(outputPath, pdf.content);
            console.log(`✅ 成功生成 PDF: ${outputPath}`);
            return outputPath;
        }
    } catch (error) {
        console.error('❌ 转换失败:', error.message);
        return null;
    }
}

// 命令行使用
if (require.main === module) {
    const args = process.argv.slice(2);
    const inputFile = args[0] || '智能办公助手_软件开发设计文档.md';
    const outputFile = args[1];
    
    convertMdToPdf(inputFile, outputFile);
}

module.exports = { convertMdToPdf }; 