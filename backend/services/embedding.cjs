const axios = require('axios');

async function getDeepSeekEmbedding(text) {
  const apiKey = process.env.DEEPSEEK_API_KEY;
  const resp = await axios.post(
    'https://api.deepseek.com/v1/embeddings',
    {
      model: 'deepseek-embedding',
      input: text
    },
    { headers: { Authorization: `Bearer ${apiKey}` } }
  );
  return resp.data.data[0].embedding;
}

module.exports = { getDeepSeekEmbedding }; 