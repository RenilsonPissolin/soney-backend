const { gerarConteudoSoney } = require('./soneyAgent');

async function testar() {
  console.log('🚀 Gerando roteiro com a Soney (Compute API)...');
  try {
    const resultado = await gerarConteudoSoney('Crie um roteiro curto de mistério no Roblox');
    console.log('\n========================================');
    console.log('🎬 FALA DA SONEY:');
    console.log(resultado.fala);
    console.log('\n📝 LEGENDA:');
    console.log(resultado.legenda);
    console.log('\n📄 TEXTO COMPLETO:');
    console.log(resultado.texto_completo);
    console.log('========================================');
  } catch (error) {
    console.error('❌ Erro na execução:');
    console.error(error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', JSON.stringify(error.response.data, null, 2));
    }
  }
}

testar();