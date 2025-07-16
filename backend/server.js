const express = require('express')
const sqlite3 = require('sqlite3').verbose()
const cors = require('cors')
const app = express()
const db = new sqlite3.Database('./db.sqlite')

app.use(cors())
app.use(express.json())

// 初始化表
const initSql = [
  `CREATE TABLE IF NOT EXISTS docs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    html_content TEXT,
    upload_time TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    doc_id INTEGER,
    create_time TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS rag_topics (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS rag_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id TEXT,
    role TEXT,
    content TEXT,
    doc_id INTEGER,
    kb_id INTEGER,
    created_at TEXT
  )`
]
initSql.forEach(sql => db.run(sql))

// 文档上传（简化为直接POST JSON）
app.post('/api/doc/upload', (req, res) => {
  const { filename, html_content } = req.body
  db.run(
    `INSERT INTO docs (filename, html_content, upload_time) VALUES (?, ?, datetime('now'))`,
    [filename, html_content],
    function (err) {
      if (err) return res.status(500).json({ error: err.message })
      res.json({ id: this.lastID })
    }
  )
})
// 文档查询
app.get('/api/doc/search', (req, res) => {
  const { q = '', page = 1, size = 20 } = req.query
  db.all(
    `SELECT * FROM docs WHERE filename LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?`,
    [`%${q}%`, size, (page - 1) * size],
    (err, rows) => {
      if (err) return res.status(500).json({ error: err.message })
      res.json(rows)
    }
  )
})
// 文档删除
app.delete('/api/doc/:id', (req, res) => {
  db.run(`DELETE FROM docs WHERE id = ?`, [req.params.id], function (err) {
    if (err) return res.status(500).json({ error: err.message })
    res.json({ success: true })
  })
})
// 知识库推送
app.post('/api/knowledge/import', (req, res) => {
  const { docId, title, content } = req.body
  db.run(
    `INSERT INTO knowledge (title, content, doc_id, create_time) VALUES (?, ?, ?, datetime('now'))`,
    [title, content, docId],
    function (err) {
      if (err) return res.status(500).json({ error: err.message })
      res.json({ id: this.lastID })
    }
  )
})
// 知识库查询
app.get('/api/knowledge', (req, res) => {
  db.all(`SELECT * FROM knowledge ORDER BY id DESC`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message })
    res.json(rows)
  })
})
// 知识库详情
app.get('/api/knowledge/:id', (req, res) => {
  db.get(`SELECT * FROM knowledge WHERE id = ?`, [req.params.id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message })
    res.json(row)
  })
})
// RAG话题
app.get('/api/rag/topics', (req, res) => {
  db.all(`SELECT * FROM rag_topics ORDER BY created_at DESC`, [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message })
    res.json(rows)
  })
})
app.post('/api/rag/topic', (req, res) => {
  const { id, title } = req.body
  db.run(
    `INSERT INTO rag_topics (id, title, created_at) VALUES (?, ?, datetime('now'))`,
    [id, title || ''],
    function (err) {
      if (err) return res.status(500).json({ error: err.message })
      res.json({ success: true })
    }
  )
})
app.delete('/api/rag/topic/:id', (req, res) => {
  db.run(`DELETE FROM rag_topics WHERE id = ?`, [req.params.id], function (err) {
    if (err) return res.status(500).json({ error: err.message })
    db.run(`DELETE FROM rag_messages WHERE topic_id = ?`, [req.params.id])
    res.json({ success: true })
  })
})
// RAG消息
app.get('/api/rag/topic/:id/messages', (req, res) => {
  db.all(
    `SELECT * FROM rag_messages WHERE topic_id = ? ORDER BY created_at ASC`,
    [req.params.id],
    (err, rows) => {
      if (err) return res.status(500).json({ error: err.message })
      res.json(rows)
    }
  )
})
app.post('/api/rag/topic/:id/message', (req, res) => {
  const { role, content, docId, kbId } = req.body
  db.run(
    `INSERT INTO rag_messages (topic_id, role, content, doc_id, kb_id, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))`,
    [req.params.id, role, content, docId || null, kbId || null],
    function (err) {
      if (err) return res.status(500).json({ error: err.message })
      res.json({ success: true })
    }
  )
})
// 智能助手RAG对话（示例，需集成大模型）
app.post('/api/doc/rag-search', async (req, res) => {
  const { question, history } = req.body
  let answer = '这是AI助手的回复（请集成大模型API）'
  let docId = null, kbId = null
  const lastMsg = history[history.length - 1]
  if (lastMsg && lastMsg.docId) docId = lastMsg.docId
  if (lastMsg && lastMsg.kbId) kbId = lastMsg.kbId
  res.json({ answer, docId, kbId })
})

// 发送验证码接口（加上详细异常捕获和日志）
app.post('/api/send-captcha', (req, res) => {
  try {
    console.log('收到请求体:', req.body, '类型:', typeof req.body, 'isArray:', Array.isArray(req.body));
    if (!req.body || typeof req.body !== 'object') {
      console.error('请求体格式错误:', req.body);
      return res.status(400).json({ code: 2, msg: '请求体格式错误', detail: req.body, type: typeof req.body });
    }
    if (!('contact' in req.body)) {
      console.error('请求体缺少contact字段:', req.body);
      return res.status(400).json({ code: 3, msg: '请求体缺少contact字段', detail: req.body });
    }
    const { contact } = req.body;
    if (!contact) {
      console.error('contact字段为空:', req.body);
      return res.status(400).json({ code: 1, msg: '缺少邮箱' });
    }
    res.json({ code: 0, msg: '验证码已发送' });
  } catch (err) {
    console.error('send-captcha接口异常:', err);
    res.status(500).json({ code: 500, msg: '服务器异常', detail: String(err) });
  }
});

app.listen(3006, () => console.log('Server running on http://localhost:3006'))

process.on('uncaughtException', (err) => {
  console.error('未捕获异常:', err);
});
process.on('unhandledRejection', (reason, promise) => {
  console.error('未处理的Promise拒绝:', reason);
});

app.use((err, req, res, next) => {
  console.error('Express错误:', err);
  res.status(500).json({ error: err.message || '服务器内部错误' });
}); 