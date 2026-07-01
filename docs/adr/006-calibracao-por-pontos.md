# ADR 006 — Calibração por pontos e tara (null) por canal

## Status

Aceito (decisões de design fechadas em 23/06/2026, fundamentadas na pesquisa do FlexLogger/DAQmx —
ver [referencia-flexlogger.md](../referencia-flexlogger.md) e [ADR-008](008-paridade-funcional-flexlogger.md)).
**Revisado em 25/06/2026** (ver "Resolução" no fim): o método de calibração **padrão passou a ser a
regressão linear**, espelhando o AqDados — consequência da virada de norte do
[ADR-010](010-paridade-com-o-lynx.md). A interpolação por segmento (herdada do FlexLogger) virou
opt-in.

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

### Resolução (25/06/2026)

Pendências resolvidas ao mexer na calibração (Fase 3). A investigação da **fonte real do domínio**
— o site da OFM (`codigo/ofm-engenharia/`, ver `components/AcervoTecnico.tsx`) e a documentação da
Lynx ("calibração por **regressão linear** de leituras") — confirmou que o tio **fabrica e calibra
células de carga** e que o método de aferição dele no AqDados é a **regressão linear**. A
interpolação por segmento veio do FlexLogger, que **deixou de ser o norte** (ADR-010). Ver
[onde-pesquisar.md](../onde-pesquisar.md).

Decisões:

1. **Regressão linear é o método padrão** quando o canal declara `pontos`. Ajusta **uma reta a N
   pontos** por mínimos quadrados (`dominio/regressao.py`, value object `Reta(a, b, correlacao)`),
   pré-computada na carga da config e aplicada em `converter`. A reta **extrapola** fora da faixa
   (relação física linear), sem clamp.
2. **Correlação (R de Pearson) é exposta** em `Reta.correlacao` — o indicador "100,00 %" do AqDados.
   Por ora só fica disponível (sem aviso/bloqueio); um limiar de qualidade dependerá da UX de
   calibração e do que o tio considera aceitável.
3. **Interpolação por segmento vira opt-in:** `metodo = "segmento"` na config, para sensores
   comprovadamente não-lineares (mantém ordenação + unicidade de volts e clamp). `metodo` default =
   `"regressao"`. A regressão **aceita volts repetido** (medições repetidas no mesmo ponto), onde ela
   justamente tolera o ruído; o segmento não (seria curva ambígua).

Pendente ainda: o modo **"Ganho e Ponto de Referência"** do AqDados (reparametrização do linear) —
adiado por ser redutível ao `ganho`/`offset` atual e de menor valor imediato.

### Alerta de correlação baixa (01/07/2026)

Resolvida a pendência 2 acima (o **limiar de qualidade** da correlação). Na aferição pela UI
([ADR-017](017-afericao-na-ui-e-escrita-de-config.md)), correlação **abaixo de 95%** passa a
**avisar** (pinta a correlação e mostra um texto), mas **não bloqueia** o Aplicar: quem decide se a
calibração está boa é o operador (o tio), como já vale para o resto do fluxo. O limiar é uma
constante no Presenter (`Afericao.CORRELACAO_MINIMA`), fácil de ajustar se o tio pedir outro valor;
sem reta (poucos pontos / tensão sem variação) não há o que alertar. Fecha o item 🟠 "alerta de
correlação baixa" das Urgências em [tarefas-futuras.md](../tarefas-futuras.md).

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
