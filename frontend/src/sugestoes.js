// Banco de perguntas sugeridas mostradas no chat (empty state e pílulas
// flutuantes). Organizado por categoria para o sorteio garantir variedade:
// cada rodada mostra perguntas de categorias diferentes, cobrindo as
// capacidades do agente (leituras das estações, dados técnicos do Windy,
// operações de campo, cadastro, região, agenda).
// As perguntas citam APENAS produtores/propriedades/cidades/culturas que
// existem nas planilhas (cidades: Porto Alegre, Caxias do Sul, Pelotas,
// Três de Maio, Gravataí, São Leopoldo), para toda sugestão clicada retornar
// dado de verdade — ao editar, confira as planilhas antes de citar um nome.
// Diretriz de conteúdo: o Windy fornece DADOS TÉCNICOS (vento médio, rajada,
// umidade relativa, ponto de orvalho, temperatura mín/máx) — as sugestões
// pedem essas métricas específicas, nunca "previsão do tempo" genérica nem
// "vai chover?". Chuva só aparece como dado registrado na planilha de leituras.
const BANCO_DE_SUGESTOES = [
  {
    categoria: "clima-agora",
    perguntas: [
      "Como estão as condições climáticas na propriedade do João Silva?",
      "Quais produtores registraram chuva nas últimas leituras?",
      "Onde está ventando mais forte entre as estações?",
      "Como está a umidade nas lavouras de Três de Maio?",
    ],
  },
  {
    categoria: "dados-tecnicos",
    perguntas: [
      "Quais as temperaturas mínima e máxima dos próximos 3 dias na Fazenda Sol Nascente?",
      "Qual a rajada máxima de vento esperada amanhã nas propriedades de soja?",
      "Qual o ponto de orvalho mínimo dos próximos dias na propriedade do Pedro Souza?",
      "Qual a umidade relativa mínima esperada esta semana no Rancho Fundo da Ana Costa?",
    ],
  },
  {
    categoria: "operacoes",
    perguntas: [
      "Amanhã dá para pulverizar na propriedade da Maria Oliveira? Me traga vento médio e rajadas.",
      "Qual dia da semana terá o vento mais fraco na lavoura de trigo da Lúcia Almeida?",
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
      "Compare o vento e a umidade entre Porto Alegre e Três de Maio nos próximos dias.",
      "Qual a temperatura mínima esperada em Pelotas no fim de semana?",
      "Qual a rajada máxima de vento esperada em Caxias do Sul nos próximos 5 dias?",
    ],
  },
  {
    categoria: "agenda",
    perguntas: [
      "Tenho visitas agendadas esta semana? Me traga temperatura e vento esperados em cada uma.",
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
