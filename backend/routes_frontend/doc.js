const express = require('express');
const multer = require('multer');
const mammoth = require('mammoth');
const xlsx = require('xlsx');
const fs = require('fs');
const path = require('path');
const db = require('../models/doc');
const { getSummary } = require('../services/ai');

const router = express.Router();
const upload = multer({ dest: 'uploads/' });

// 上传文档
router.post('/upload', upload.single('file'), async (req, res) => {
  const file = req.file;
  let content = '';
  const ext = path.extname(file.originalname).toLowerCase();

  try {
    if (ext === '.txt') {
      content = fs.readFileSync(file.path, 'utf-8');
    } else if (ext === '.docx') {
      const result = await mammoth.extractRawText({ path: file.path });
      content = result.value;
    } else if (ext === '.xls' || ext === '.xlsx' || ext === '.csv') {
      const workbook = xlsx.readFile(file.path);
      content = JSON.stringify(xlsx.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]]));
    } else {
      return res.status(400).json({ error: '不支持的文件类型' });
    }

    // 保存解析内容
    const parsedPath = `parsed/${file.filename}.txt`;
    fs.writeFileSync(parsedPath, content);

    // 存数据库
    db.run(
      `INSERT INTO documents (filename, filepath, content, type) VALUES (?, ?, ?, ?)`,
      [file.originalname, file.path, content, ext],
      function (err) {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ id: this.lastID, message: '上传并解析成功' });
      }
    );
  } catch (err) {
    res.status(500).json({ error: '解析失败', detail: err.message });
  }
});

// 文档检索
router.get('/search', (req, res) => {
  const { q } = req.query;
  db.all(
    `SELECT id, filename, substr(content,1,200) as snippet, upload_time FROM documents WHERE content LIKE ? ORDER BY upload_time DESC`,
    [`%${q || ''}%`],
    (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json(rows);
    }
  );
});

// 智能摘要
router.post('/summary', async (req, res) => {
  const { id } = req.body;
  db.get(`SELECT content FROM documents WHERE id = ?`, [id], async (err, row) => {
    if (err || !row) return res.status(404).json({ error: '文档不存在' });
    try {
      const summary = await getSummary(row.content.slice(0, 2000));
      res.json({ summary });
    } catch (e) {
      res.status(500).json({ error: '大模型调用失败', detail: e.message });
    }
  });
});

module.exports = router; 