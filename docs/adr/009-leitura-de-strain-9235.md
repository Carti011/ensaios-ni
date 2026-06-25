# ADR 009 — Leitura de strain do 9235

## Status

Aceito — testado por mock no Mac e **validado no Windows simulado em 25/06/2026**: o `daqmx` leu o
9235 simulado (finito e contínuo) sem erro, com quarter-bridge / 120 Ω / 2,0 V confirmados. O
**número físico** (bater com o test panel sobre carga conhecida) fica para o hardware (Fase 4).
Ver [validacao-windows.md](../validacao-windows.md).

## Contexto

O [ADR-005](005-contrato-multicanal-da-porta.md) entregou a leitura de **tensão** (9205) e deixou
explícito que "a porta provavelmente ganhará um método irmão para strain", à espera do gage factor
do dono. A rodada 2 (22/06/2026) trouxe os parâmetros do 9235: **quarter-bridge 120 Ω**, gage
factor **2,14–2,16** (varia por lote), **3 fios** (cabo longo), saída em **microstrain**, com
**null/tara**.

A armadilha que define o cuidado desta fatia: os **defaults de `add_ai_strain_gage_chan` são
full-bridge 350 Ω / 2,5 V**. Rodar sem trocá-los produz **número plausível e errado, sem lançar
erro** (contexto-hardware §4). É o maior risco técnico do projeto.

## Decisão

- **A porta ganha um método irmão** `ler_strain(canais, amostras, taxa_hz) -> dict[str, list[float]]`,
  em **task separada** da tensão (tipo de medição diferente — não se mistura na mesma task).
- **O driver NI aplica gage factor + ponte** (`add_ai_strain_gage_chan`, `units=STRAIN`) e devolve
  **strain adimensional**. É coerente com a [paridade FlexLogger/NI](008-paridade-funcional-flexlogger.md):
  não reimplementamos a física da ponte, usamos a do driver.
- **`ConfigStrain`** (dataclass em `aquisicao/daqmx.py`) fixa os parâmetros do 9235 e seus
  **defaults são os do 9235 — JAMAIS os da API**: `QUARTER_BRIDGE_I`, 120 Ω, excitação **interna**
  2,0 V, gage factor 2,15 (meio da faixa, **configurável**), `lead_wire_resistance` para os 3 fios,
  poisson 0,3.
- **microstrain não exige código de domínio novo:** é um **canal linear com ganho 1.000.000**
  (`strain × 1e6`), reusando `converter()` e `calcular_tara` ([ADR-006](006-calibracao-por-pontos.md)).
- **Teste-guarda anti-armadilha:** um teste afirma que a task recebe quarter-bridge / 120 Ω / 2,0 V
  (e o gage factor configurado) — falha imediatamente se algum dia o código cair nos defaults da API.
- **Aquisição finita** (`FINITE`) + **sample clock obrigatório** (o 9235 delta-sigma falha on-demand
  no chassi Ethernet). Import `nidaqmx` **lazy**, só no `daqmx.py`.

## Consequências

**Melhora:**

- A parte de maior risco fica protegida por teste automatizado, no Mac, sem hardware.
- microstrain e tara saem de graça do domínio já existente (sem duplicação).
- Vocabulário e física alinhados ao NI/FlexLogger — transição natural para o dono.

**Piora / pendente:**

- O mock prova que montamos a task certo, **não** que o número físico bate. Validação objetiva
  continua sendo contra o **test panel do NI-MAX** (Windows/hardware).
- **Gage factor é por-task** no MVP (uma `ConfigStrain` por adaptador), não por-canal — refina
  quando o dono mandar os valores reais por extensômetro (rodada 3).
- **Integração tensão + strain no `executar_ensaio`/CLI: FEITO** (25/06/2026). O caso de uso
  particiona os canais pelo campo `tipo` (`tensao`/`strain`), lê cada grupo na sua task e grava
  tudo num CSV, na ordem do config; a tara vale para os dois tipos. A demo do Mac já exibe
  microstrain. Strain ainda exige Windows para validar o número físico (test panel do NI-MAX).
- **Sincronização por hardware start-trigger entre as tasks de tensão e strain: pendente.** No MVP
  as duas tasks são FINITE com a mesma taxa e nº de amostras, lidas em sequência — o eixo de tempo
  do CSV é coerente, mas há um pequeno offset de início entre elas. Para carga × deformação e FFT de
  precisão, o ideal é um **start trigger compartilhado** (ou sample clock comum) no `daqmx.py`.
  Código que só roda/valida no Windows; avaliar prioridade na validação em hardware (Fase 4).
- Aquisição **contínua** de longa duração segue pendente ([ADR-007](007-aquisicao-continua.md)).
