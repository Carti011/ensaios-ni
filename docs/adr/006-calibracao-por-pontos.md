# ADR 006 — Calibração por pontos e tara (null) por canal

## Status

Aceito (decisões de design fechadas em 23/06/2026, fundamentadas na pesquisa do FlexLogger/DAQmx —
ver [referencia-flexlogger.md](../referencia-flexlogger.md) e [ADR-008](008-paridade-funcional-flexlogger.md))

## Contexto

O [ADR-002](002-conversao-linear-e-contrato-da-porta.md) assumiu que a conversão volts→unidade
de engenharia seria **linear, fixa em config** (`valor = ganho * volts + offset`). Era uma
aposta razoável com a informação que tínhamos. As respostas do dono do hardware (áudios de
22/06/2026, em [respostas-tio.md](../respostas-tio.md)) mostram que **não é assim que ele
trabalha**:

- A correlação voltagem→engenharia **depende de cada sensor** e ele não tem fórmulas prontas.
- Ele **calibra empiricamente por pontos**: aplica uma carga conhecida, lê a voltagem
  correspondente e **vai construindo a curva** ponto a ponto — exatamente o "canal de
  calibração" do **AqDados (Lynx)**, software de referência dele.
- Antes de cada ensaio ele faz a **tara/null**: lê a tensão de repouso e a declara como zero.
- Para strain, lê e multiplica por 1.000.000 para obter **microstrain**.

Ou seja: a conversão é uma **função de calibração por canal, derivada de pontos medidos**, com
um **offset de zero dinâmico** (a tara), e não um par fixo de coeficientes hardcoded.

## Decisão

- **A conversão de um canal passa a ser uma calibração derivada de pontos `(volts, valor)`.**
  Dois pontos produzem uma reta (interpolação linear); mais pontos permitem curva por partes
  (decisão de interpolação — linear por segmento como padrão — fica para a implementação).
- **O `ganho·V + offset` do ADR-002 vira o caso particular de 2 pontos** e continua válido para
  os sensores que já têm coeficientes conhecidos. A config (`config/canais.toml`) ganha a opção
  de declarar **pontos de calibração** por canal além de ganho/offset.
- **Tara (null) por canal** é uma operação explícita no início do ensaio: captura a tensão de
  repouso e a subtrai como zero. Fica no domínio (não no adaptador), parametrizável e auditável.
- **microstrain** é uma unidade de saída de primeira classe para canais de strain.
- A calibração e a tara vivem no **domínio** (testáveis no Mac, sem `nidaqmx`); a aquisição
  continua devolvendo volts brutos (ADR-002/005 seguem valendo nesse ponto).

### Decisões de design fechadas (23/06/2026)

A pesquisa do FlexLogger/NI-DAQmx fundamentou as três decisões que estavam abertas. Em todas, a
escolha é **fazer como o FlexLogger** (que é o padrão das Custom Scales do DAQmx — ver
[referencia-flexlogger.md](../referencia-flexlogger.md)):

- **(a) Formato na config** — `pontos = [[volts, valor], ...]` por canal; **na ausência**, cai pro
  `ganho`/`offset` linear do ADR-002. Equivale às escalas **Table** e **Linear** do DAQmx, que o
  FlexLogger expõe lado a lado. Dois pontos = a reta atual. Retrocompatível.
- **(b) Fora da faixa de calibração** — **clamp** (satura no ponto extremo mais próximo),
  espelhando o *"Read operations will clip samples outside the table"* do DAQmx. **Não** é
  extrapolação nem erro. Distinto de **remoção de outliers**, que é etapa de análise/pós-
  processamento (futura, estilo AqDAnalysis), não da conversão.
- **(c) Tara (null)** — replica o **"Zero Channel"** do FlexLogger: lê N amostras de repouso,
  calcula a **média** e a subtrai como zero. Operação **separada da calibração**, opcional por
  canal, no domínio.

### Modelo de interpolação

Interpolação **linear por segmento** entre pontos (igual à Table scale do DAQmx). Polinômio/spline
fica reservado para quando houver pontos reais que justifiquem.

### Refinamento a partir das telas do AqDados (24/06/2026) — pendente

Os prints do AqDados ([referencia-lynx.md §1.2–1.3](../referencia-lynx.md)) mostram que o método de
calibração do dono é mais rico do que o assumido aqui. O menu "Aferir" tem **dois modos**:

- **por Regressão Linear** — ajusta **uma única reta a N pontos** (mínimos quadrados) e reporta a
  **correlação** (R, ex.: "100,00 %"). Tolera ruído de medição. **Difere** da nossa interpolação por
  segmento (que passa exatamente por cada ponto).
- **por Ganho e Ponto de Referência** — ganho + um ponto de referência (offset/tara declarada).

Pendência a decidir quando formos mexer na calibração (provável Fase 3):

1. Suportar **regressão linear** (além da interpolação por segmento) como modo de escala.
2. Expor a **correlação** ao usuário como indicador de qualidade do ajuste.
3. Avaliar o modo **"Ganho e Ponto de Referência"** vs a nossa tara atual.

Não resolver agora — só registrado para não se perder. A interpolação por segmento segue como
comportamento atual.

## Consequências

**Melhora:**

- O número finalmente vira grandeza física do jeito que o dono valida — replica o fluxo do
  AqDados, removendo a dependência do FlexLogger.
- Cobre sensores sem fórmula fechada (a maioria, segundo o dono).

**Piora / pendente:**

- Exige uma **UX de calibração** (capturar pontos aplicando carga conhecida) — provavelmente
  parte da Fase 3 (dashboard) ou um modo de CLI dedicado. Maior esforço que o linear.
- ~~Estratégia de **interpolação** ainda não decidida~~ → **decidida: linear por segmento** (Table
  scale do DAQmx). Polinômio/spline só se pontos reais justificarem.
- Persistência da **tabela de calibração** e do **valor de tara** por ensaio (rastreabilidade)
  ainda a definir.
- Falta confirmar com o dono o **formato de arquivo** para compatibilidade com AqDados/AqDAnalysis.
