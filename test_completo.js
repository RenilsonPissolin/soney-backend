// test_completo.js — Testa o fluxo completo: gerar + publicar
const { gerarEPublicar } = require('./soneyAgent');

async function testar() {
  console.log('🚀 SONEY — FLUXO COMPLETO: GERAR + PUBLICAR');
  console.log('='.repeat(50));

  try {
    const resultado = await gerarEPublicar(
      'Crie um roteiro curto de mistério no Roblox sobre um relógio misterioso'
    );

    console.log('\n✅ ROTEIRO GERADO E PUBLICADO COM SUCESSO!');
    console.log('='.repeat(50));
    console.log('🎬 FALA:', resultado.fala.slice(0, 100) + '...');
    console.log('📝 LEGENDA:', resultado.legenda.slice(0, 100) + '...');

  } catch (error) {
    console.error('❌ Erro no fluxo completo:', error.message);
  }
}

testar();