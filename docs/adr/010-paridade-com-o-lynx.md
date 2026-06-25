# ADR 010 — Paridade com o Lynx (AqDados + AqDAnalysis) como referência primária

## Status

Aceito (24/06/2026). **Revisa o [ADR-008](008-paridade-funcional-flexlogger.md)**, que passa a
valer só na parte técnica de baixo nível.

## Contexto

O [ADR-008](008-paridade-funcional-flexlogger.md) definiu o **FlexLogger** como norte de paridade,
partindo da premissa de que era o software que o dono "já usa e está satisfeito". Em 23/06/2026 o
dono enviou prints dos softwares que realmente usa e esclareceu, textualmente:

> "Se for para copiar um programa o ideal seria o **AqDados e AqDAnalisis juntos**... porque **eu
> já domino**. Já o **FlexLogger, estou aprendendo a mexer agora**."

Ou seja, a premissa do ADR-008 estava **invertida**: o software que ele domina há anos é o par
**Lynx (AqDados + AqDAnalysis)**; o FlexLogger é o que ele está aprendendo agora (e está num trial
pago, "expira em 37 dias"). Os prints (analisados em [referencia-lynx.md](../referencia-lynx.md))
mostram o modelo mental, o vocabulário e o fluxo que ele conhece.

Como o objetivo do projeto é **adoção pelo dono** (ele largar o software pago e usar o nosso), o
software deve ser o mais reconhecível possível **para ele** — e isso significa espelhar o **Lynx**,
não o FlexLogger.

## Decisão

**A referência primária de UX, vocabulário e fluxo de trabalho passa a ser o Lynx (AqDados +
AqDAnalysis).** O FlexLogger é rebaixado a **referência técnica de baixo nível** apenas — porque por
baixo ele expõe o NI-DAQmx, que é o driver que o nosso adaptador usa de qualquer jeito.

Concretamente:

- **Aquisição/configuração** espelha o **AqDados**: tabela de canais (nome do sinal, unidade, tipo,
  faixa, limites), aferição (calibração) por canal, balanço/repouso (tara). Ver
  [referencia-lynx.md §1](../referencia-lynx.md).
- **Vocabulário** segue o do Lynx (Sinal, Aferição, Balanço, Repouso, Consulta, Sinais, Eventos),
  que o dono já pensa. Atualizado no [CONTEXT.md](../../CONTEXT.md).
- **Análise** **não** é reescrita: interoperamos com o AqDAnalysis exportando **TXT** — ver
  [ADR-011](011-estrategia-de-exportacao.md).
- **Calibração** ganha um ponto a refinar: o AqDados oferece **Regressão Linear** e **Ganho e Ponto
  de Referência**, além de mostrar **correlação**; o [ADR-006](006-calibracao-por-pontos.md) hoje só
  prevê interpolação por segmento. Refinamento registrado lá.

**O que do ADR-008 continua valendo:** a parte técnica. "Seguir o padrão NI-DAQmx" segue correto
para o **comportamento do driver** (Custom Scales, clamp na leitura, sample clock, parâmetros de
strain), porque é o driver que o nosso `daqmx.py` opera. O que muda é que o **espelho de produto**
(o que o usuário vê e o vocabulário) passa a ser o Lynx, não o FlexLogger.

**Regra operacional atualizada (substitui a do ADR-008):** em dúvida de **comportamento de produto**
(como calibrar, zerar, organizar telas, nomear coisas), pesquisar **como o AqDados/AqDAnalysis faz**
e registrar em [referencia-lynx.md](../referencia-lynx.md). Em dúvida de **comportamento técnico do
driver** (conversão de escala, timing, faixa, parâmetros de hardware), continuar pesquisando o
**NI-DAQmx/FlexLogger** e registrar em [referencia-flexlogger.md](../referencia-flexlogger.md).

## Consequências

**Melhora:**

- Maior chance de adoção real: o dono reconhece o software no que ele já domina, não no que está
  aprendendo.
- A estratégia de **não reescrever a análise** (interoperar via TXT) reduz drasticamente o escopo —
  ver [ADR-011](011-estrategia-de-exportacao.md).
- Vocabulário e fluxo ganham uma referência concreta (os prints), não suposições.

**Piora / pendente:**

- O ADR-008 fica **parcialmente substituído**; é preciso ler os dois juntos (008 para o nível do
  driver, 010 para o nível de produto).
- A calibração precisa ser revisada para cobrir os dois modos do AqDados (regressão + ponto de
  referência) e a correlação — ver [ADR-006](006-calibracao-por-pontos.md).
- O layout exato do TXT importável pelo AqDAnalysis ainda é incógnita — ver
  [ADR-011](011-estrategia-de-exportacao.md).
