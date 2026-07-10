// Banco de perguntas sugeridas mostradas no chat (empty state e chips acima do
// input). Organizado por categoria para o sorteio garantir variedade: cada
// rodada mostra perguntas de categorias diferentes, cobrindo as capacidades do
// agente (clima atual, previsão, operações de campo, cadastro, região, agenda).
// As perguntas citam produtores/cidades/culturas que existem nas planilhas de
// exemplo, para toda sugestão clicada retornar dado de verdade.
const BANCO_DE_SUGESTOES = [
  {
    categoria: "clima-agora",
    perguntas: [
      "Como estão as condições climáticas na propriedade do João Silva?",
      "Quais produtores registraram chuva nas últimas leituras?",
      "Onde está ventando mais forte entre as estações?",
      "Como está a umidade nas lavouras de Santa Rosa?",
    ],
  },
  {
    categoria: "previsao",
    perguntas: [
      "Qual a previsão do tempo para a Fazenda Sol Nascente nos próximos 3 dias?",
      "Vai chover esta semana nas propriedades que plantam soja?",
      "Qual a temperatura mínima prevista para a propriedade do Pedro Souza?",
    ],
  },
  {
    categoria: "operacoes",
    perguntas: [
      "Amanhã dá para pulverizar na propriedade da Maria Oliveira? Como estará o vento?",
      "Qual o melhor dia da semana para colher trigo, considerando a chuva prevista?",
      "Em quais propriedades o vento passa de 15 km/h amanhã?",
    ],
  },
  {
    categoria: "produtores-culturas",
    perguntas: [
      "Quais produtores cultivam soja?",
      "Liste as propriedades com mais de 100 hectares.",
      "Qual a área total cadastrada por cultura?",
      "Quais culturas temos cadastradas e em quais cidades?",
    ],
  },
  {
    categoria: "regiao",
    perguntas: [
      "Como estará o tempo em Santo Cristo no fim de semana?",
      "Compare a previsão de chuva entre Santa Rosa e São Luiz Gonzaga.",
      "Qual a previsão para São Luiz Gonzaga nos próximos 5 dias?",
    ],
  },
  {
    categoria: "agenda",
    perguntas: [
      "Tenho visitas agendadas esta semana? Como estará o tempo em cada uma?",
      "Quais compromissos tenho na agenda dos próximos 7 dias?",
    ],
  },
];

// Embaralha uma cópia do array (Fisher-Yates).
function embaralhar(itens) {
  const copia = itens.slice();
  for (let i = copia.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copia[i], copia[j]] = [copia[j], copia[i]];
  }
  return copia;
}

// Sorteia `n` perguntas, cada uma de uma categoria distinta — nunca duas do
// mesmo tipo na mesma rodada.
export function sortearSugestoes(n = 3) {
  return embaralhar(BANCO_DE_SUGESTOES)
    .slice(0, n)
    .map(({ perguntas }) => perguntas[Math.floor(Math.random() * perguntas.length)]);
}
