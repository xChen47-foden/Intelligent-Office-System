require('dotenv').config();
const axios = require('axios');

async function getSummary(content) {
  const apiKey = process.env.OPENAI_API_KEY;
  const resp = await axios.post(
    'https://api.openai.com/v1/chat/completions',
    {
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'system', content: '你是一个文档摘要助手，请用简洁中文总结以下内容：' },
        { role: 'user', content }
      ]
    },
    {
      headers: { Authorization: `Bearer ${apiKey}` }
    }
  );
  return resp.data.choices[0].message.content;
}

module.exports = { getSummary }; 