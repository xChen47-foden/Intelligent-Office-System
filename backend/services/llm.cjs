const axios = require('axios');

async function callDeepSeek(messages) {
  const apiKey = process.env.DEEPSEEK_API_KEY;
  const resp = await axios.post(
    'https://api.deepseek.com/v1/chat/completions',
    {
      model: 'deepseek-chat',
      messages
    },
    { headers: { Authorization: `Bearer ${apiKey}` } }
  );
  return resp.data.choices[0].message.content;
}

module.exports = { callDeepSeek }; 