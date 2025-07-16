const express = require('express');
const multer = require('multer');
const mammoth = require('mammoth');
const xlsx = require('xlsx');
const fs = require('fs');
const path = require('path');
const db = require('../models/doc.cjs');
const { getSummary } = require('../services/ai.cjs');
const officeParser = require('officeparser');
const axios = require('axios');
const chunkDb = require('../models/doc_chunk.cjs');
const { callDeepSeek } = require('../services/llm.cjs');
const { getDeepSeekEmbedding } = require('../services/embedding.cjs');

const router = express.Router();
const upload = multer({ dest: 'uploads/' });

// 处理中文文件名乱码
function fixFilename(name) {
  return Buffer.from(name, 'latin1').toString('utf8');
}

// 上传文档
router.post('/upload', upload.single('file'), async (req, res) => {
  const file = req.file;
  // 修正文件名
  const fixedFilename = fixFilename(file.originalname);
  let content = '';
  const ext = path.extname(fixedFilename).toLowerCase();

  try {
    if (ext === '.txt') {
      content = fs.readFileSync(file.path, 'utf-8');
    } else if (ext === '.docx') {
      const result = await mammoth.extractRawText({ path: file.path });
      content = result.value;
    } else if (ext === '.pptx') {
      // 使用 officeparser 解析 pptx
      content = await new Promise((resolve, reject) => {
        officeParser.parseOfficeAsync(file.path, function(data, err) {
          if (err) return reject(err);
          resolve(data);
        });
      });
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
      [fixedFilename, file.path, content, ext],
      async function (err) {
        if (err) return res.status(500).json({ error: err.message });
        // 分段并生成embedding
        await splitAndStoreChunks(this.lastID, content);
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
  let sql = 'SELECT id, filename, substr(content,1,200) as snippet, upload_time FROM documents';
  let params = [];
  if (q && q.trim() !== '') {
    sql += ' WHERE content LIKE ?';
    params.push(`%${q}%`);
  }
  sql += ' ORDER BY upload_time DESC';
  db.all(sql, params, (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
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

// 删除文档
router.delete('/:id', (req, res) => {
  const id = req.params.id;
  // 先查找文件路径
  db.get('SELECT filepath FROM documents WHERE id = ?', [id], (err, row) => {
    if (err || !row) return res.status(404).json({ error: '文档不存在' });
    // 删除数据库记录
    db.run('DELETE FROM documents WHERE id = ?', [id], (err2) => {
      if (err2) return res.status(500).json({ error: err2.message });
      // 删除原文件
      try { if (row.filepath && fs.existsSync(row.filepath)) fs.unlinkSync(row.filepath); } catch {}
      res.json({ message: '删除成功' });
    });
  });
});

// 下载文档全文
router.get('/:id/download', (req, res) => {
  const id = req.params.id;
  db.get('SELECT filename, content FROM documents WHERE id = ?', [id], (err, row) => {
    if (err || !row) return res.status(404).json({ error: '文档不存在' });
    res.setHeader('Content-Disposition', `attachment; filename=\"${encodeURIComponent(row.filename)}.txt\"`);
    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.send(row.content);
  });
});

// 编辑文档
router.put('/:id', async (req, res) => {
  const id = req.params.id;
  const { filename, content } = req.body;
  db.run(
    'UPDATE documents SET filename = ?, content = ? WHERE id = ?',
    [filename, content, id],
    function (err) {
      if (err) return res.status(500).json({ error: err.message });
      if (this.changes === 0) return res.status(404).json({ error: '文档不存在' });
      res.json({ message: '编辑成功' });
    }
  );
});

// 文档上传后分段并生成embedding
async function splitAndStoreChunks(docId, content) {
  const chunks = content.match(/.{1,500}/g) || [];
  for (const chunk of chunks) {
    const embedding = await getDeepSeekEmbedding(chunk);
    chunkDb.run(
      'INSERT INTO doc_chunks (doc_id, chunk, embedding) VALUES (?, ?, ?)',
      [docId, chunk, JSON.stringify(embedding)]
    );
  }
}

// 通义千问API示例（可切换为其他国产大模型）
async function callTongyiQwen(messages) {
  // 伪代码，需替换为真实API
  const apiKey = process.env.TONGYI_API_KEY;
  const resp = await axios.post(
    'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
    {
      model: 'qwen-turbo',
      input: { messages }
    },
    { headers: { Authorization: `Bearer ${apiKey}` } }
  );
  return resp.data.output.text;
}

// RAG检索接口
router.post('/rag-search', async (req, res) => {
  const { question, history = [] } = req.body;
  const qEmbedding = await getDeepSeekEmbedding(question);
  chunkDb.all('SELECT id, doc_id, chunk, embedding FROM doc_chunks', [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    function cosineSim(a, b) {
      let dot = 0, normA = 0, normB = 0;
      for (let i = 0; i < a.length; i++) {
        dot += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
      }
      return dot / (Math.sqrt(normA) * Math.sqrt(normB));
    }
    const scored = rows.map(row => ({
      ...row,
      score: cosineSim(qEmbedding, JSON.parse(row.embedding))
    }));
    scored.sort((a, b) => b.score - a.score);
    const topChunks = scored.slice(0, 5).map(row => row.chunk).join('\n\n');
    const messages = [
      { role: 'system', content: '你是一个智能文档检索助手。' },
      ...history,
      { role: 'user', content: `请结合以下文档内容，回答我的问题：\n${topChunks}\n\n我的问题：${question}` }
    ];
    callDeepSeek(messages).then(answer => {
      res.json({ answer });
    }).catch(e => {
      res.status(500).json({ error: '大模型API调用失败', detail: e.message });
    });
  });
});

// 智能助手对话接口
router.post('/chat', async (req, res) => {
  const { question, history = [] } = req.body;
  // 检索知识库相关内容
  db.all(
    'SELECT filename, content FROM documents WHERE content LIKE ? ORDER BY upload_time DESC LIMIT 5',
    [`%${question}%`],
    async (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });
      const context = rows.map(doc => `【${doc.filename}】${doc.content.slice(0, 500)}`).join('\n\n');
      const messages = [
        { role: 'system', content: '你是一个智能办公助手，能理解用户意图，结合知识库和日程等信息高效答复。' },
        ...history,
        { role: 'user', content: `请结合以下知识库内容，回答我的问题：\n${context}\n\n我的问题：${question}` }
      ];
      try {
        let answer = '';
        if (process.env.TONGYI_API_KEY) {
          // 调用通义千问
          answer = await callTongyiQwen(messages);
        } else if (process.env.OPENAI_API_KEY) {
          const resp = await axios.post(
            'https://api.openai.com/v1/chat/completions',
            { model: 'gpt-3.5-turbo', messages },
            { headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` } }
          );
          answer = resp.data.choices[0].message.content;
        } else {
          return res.status(500).json({ error: '未配置大模型API KEY' });
        }
        res.json({ answer });
      } catch (e) {
        res.status(500).json({ error: '大模型API调用失败', detail: e.message });
      }
    }
  );
});

module.exports = router; 