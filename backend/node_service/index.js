const express = require('express');
const app = express();
const port = 3007;

app.get('/', (req, res) => {
  res.json({ msg: 'Node.js 子服务已启动' });
});

app.listen(port, () => {
  console.log(`Node.js 服务运行在 http://localhost:${port}`);
}); 