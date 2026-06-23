# ADR 006 — Calibração por pontos e tara (null) por canal

## Status

Proposto

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

## Consequências

**Melhora:**

- O número finalmente vira grandeza física do jeito que o dono valida — replica o fluxo do
  AqDados, removendo a dependência do FlexLogger.
- Cobre sensores sem fórmula fechada (a maioria, segundo o dono).

**Piora / pendente:**

- Exige uma **UX de calibração** (capturar pontos aplicando carga conhecida) — provavelmente
  parte da Fase 3 (dashboard) ou um modo de CLI dedicado. Maior esforço que o linear.
- Estratégia de **interpolação** (linear por segmento vs. polinomial/spline) ainda não decidida;
  resolver quando houver pontos reais de calibração do dono.
- Persistência da **tabela de calibração** e do **valor de tara** por ensaio (rastreabilidade)
  ainda a definir.
- Falta confirmar com o dono o **formato de arquivo** para compatibilidade com AqDados/AqDAnalysis.
