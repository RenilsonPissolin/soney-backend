// soneyPublisher.js — Publica roteiros gerados pela Soney
// Opções: Google Drive API | Webhook Make

require('dotenv').config();
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// ─── CONFIG ────────────────────────────────────────────────────

const DRIVE_FOLDER_ID = process.env.GOOGLE_DRIVE_FOLDER_ID || '';
const MAKE_WEBHOOK_URL = process.env.MAKE_WEBHOOK_URL || '';
const GOOGLE_DRIVE_API_KEY = process.env.GOOGLE_DRIVE_API_KEY || '';

// ─── PUBLICAR VIA WEBHOOK (MAKE) ───────────────────────────────

async function publicarViaMake(roteiro) {
  if (!MAKE_WEBHOOK_URL) {
    console.log('⚠️ MAKE_WEBHOOK_URL não configurada. Pule o webhook.');
    return false;
  }

  console.log('📤 Enviando roteiro para Make...');
  
  const payload = {
    evento: 'novo_roteiro_soney',
    timestamp: new Date().toISOString(),
    serie: 'O Último Andar',
    conteudo: {
      fala: roteiro.fala,
      legenda: roteiro.legenda,
      texto_completo: roteiro.texto_completo
    },
    metadados: {
      modelo: 'deepseek-deepseek-v4-flash',
      plataforma: 'TikTok',
      formato: 'vertical_9_16'
    }
  };

  try {
    const response = await axios.post(MAKE_WEBHOOK_URL, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 15000
    });
    console.log('✅ Roteiro enviado ao Make!');
    return true;
  } catch (error) {
    console.error('❌ Erro ao enviar para Make:', error.message);
    return false;
  }
}

// ─── SALVAR LOCALMENTE ─────────────────────────────────────────

async function salvarLocalmente(roteiro, nomeArquivo) {
  const pasta = path.join(__dirname, 'roteiros_gerados');
  if (!fs.existsSync(pasta)) {
    fs.mkdirSync(pasta, { recursive: true });
  }

  const caminho = path.join(pasta, `${nomeArquivo}.md`);
  
  const conteudo = `# 🎬 ROTEIRO SONEY — ${new Date().toLocaleDateString('pt-BR')}
  
## Fala da Soney:
${roteiro.fala}

## Legenda:
${roteiro.legenda}

## Texto Completo:
${roteiro.texto_completo}

---
*Gerado automaticamente pelo agente Soney via Compute API Virtuals*
`;

  fs.writeFileSync(caminho, conteudo, 'utf-8');
  console.log(`✅ Roteiro salvo em: ${caminho}`);
  return caminho;
}

// ─── PUBLICAR TUDO ─────────────────────────────────────────────

async function publicarRoteiro(roteiro, nomeArquivo) {
  console.log('\n📤 PUBLICANDO ROTEIRO...');
  console.log('='.repeat(40));

  const resultados = {
    local: false,
    make: false
  };

  // 1. Salva localmente
  const caminho = await salvarLocalmente(roteiro, nomeArquivo);
  resultados.local = !!caminho;

  // 2. Envia via webhook Make
  if (MAKE_WEBHOOK_URL) {
    resultados.make = await publicarViaMake(roteiro);
  }

  // 3. Google Drive (via Make, se configurado)
  // O Make pode pegar o webhook e salvar no Google Drive automaticamente

  console.log('='.repeat(40));
  console.log('📊 RESULTADO DA PUBLICAÇÃO:');
  console.log(`   📁 Local: ${resultados.local ? '✅' : '❌'}`);
  console.log(`   🔗 Make:  ${resultados.make ? '✅' : '❌'}`);
  console.log('='.repeat(40));

  return resultados;
}

module.exports = { publicarRoteiro, salvarLocalmente, publicarViaMake };