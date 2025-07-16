const express = require('express');
const docRouter = require('./routes/doc.cjs');
const cors = require('cors');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

// 确保上传和解析目录存在
['uploads', 'parsed', 'db'].forEach(dir => {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir);
});

app.use('/api/doc', docRouter);

app.listen(3001, () => {
  console.log('智能文档后端服务已启动，端口 3001');
}); 