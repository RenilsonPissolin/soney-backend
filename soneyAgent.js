require('dotenv').config();
const axios = require('axios');
const { publicarRoteiro } = require('./soneyPublisher');

const COMPUTE_API = process.env.VIRTUALS_BASE_URL || 'https://compute.virtuals.io/v1';
const API_KEY = process.env.VIRTUALS_API_KEY;

async function gerarConteudoSoney(tema = 'Crie um roteiro curto de mistério no Roblox', publicar = true) {
  console.log('🤖 Chamando Compute API da Virtuals...');
  
  const response = await axios.post(`${COMPUTE_API}/chat/completions`, {
    model: 'deepseek-deepseek-v4-flash',
    messages: [
      {
        role: 'system',
        content: `Você é a SONEY, uma diretora de cinema digital e showrunner de minisséries dramáticas verticais para TikTok e Roblox.
Sempre responda em português brasileiro.
Gere roteiros no formato:
- Hook (0-3s): frase de impacto
- Desenvolvimento: tensão dramática
- Cliffhanger + CTA: o que o espectador deve decidir

Inclua legenda com hashtags no final.`
      },
      {
        role: 'user',
        content: tema
      }
    ],
    temperature: 0.8,
    max_tokens: 1000
  }, {
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    }
  });

  const texto = response.data.choices[0].message.content;
  
  // Extrai fala e legenda do texto gerado
  const partes = texto.split('---').map(p => p.trim());
  const fala = partes[0] || texto;
  const legenda = partes[1] || '#Soney #Roblox #Drama';

  return { fala, legenda, texto_completo: texto };
}

async function gerarEPublicar(tema = 'Crie um roteiro curto de mistério no Roblox') {
  console.log('\n🎬 SONEY — FLUXO COMPLETO');
  console.log('='.repeat(40));
  
  // 1. Gera o roteiro
  const resultado = await gerarConteudoSoney(tema, false);
  
  // 2. Publica (local + webhook)
  const nomeArquivo = `roteiro_soney_${Date.now()}`;
  await publicarRoteiro(resultado, nomeArquivo);
  
  return resultado;
}

module.exports = { gerarConteudoSoney, gerarEPublicar };