# ADR 003 — Persistência do ensaio em CSV (série temporal)

## Status

Aceito

## Contexto

Um ensaio precisa ser **registrado** para depois ser analisado e virar laudo. O domínio
do dono do hardware (OFM Engenharia — provas de carga e análise de vibração) produz
**séries temporais amostradas a taxa fixa**: o resultado não é um número solto, é o sinal
ao longo do tempo, de onde se extrai gráfico carga×deformação (estático) ou frequências
naturais via FFT (dinâmico).

O [ADR-002](002-conversao-linear-e-contrato-da-porta.md) definiu que a porta retorna
**volts brutos** (`list[float]`, sem timestamp) e que a conversão para unidade de
engenharia é linear e vive no domínio. Faltava decidir **o que e como é persistido**.

## Decisão

- **Formato CSV** (texto). Abre direto no Excel e em qualquer ferramenta de análise.
  TDMS (binário nativo da NI, melhor para alta taxa) e PostgreSQL ficam para quando a
  necessidade aparecer — não antecipar.
- **Layout "wide":** primeira coluna `tempo_s`, depois **uma coluna por canal**. É o
  formato que ferramentas de FFT/planilha esperam.
- **`tempo_s` é derivado da taxa de amostragem** (`índice / taxa_hz`), não lido do
  hardware — coerente com o ADR-002 (a porta não devolve timestamp).
- **Grava valores já convertidos** (unidade de engenharia), não volts. A **unidade vai no
  cabeçalho**: `Mod1/ai0 (kgf)`. Quem converte é o domínio; a persistência só grava.
- **A persistência é "burra":** recebe um dicionário pronto (`canal -> lista de valores`)
  e não conhece `Canal`, conversão nem aquisição.
- **Validações no momento de gravar:** `taxa_hz > 0` e todos os canais com o **mesmo
  número de amostras** (senão `ValueError` claro, em vez de truncar ou estourar índice).

## Consequências

**Melhora:**

- Resultado imediatamente utilizável (planilha/FFT), sem passo de conversão externo.
- Responsabilidades separadas: aquisição lê, domínio converte, persistência grava.
- Erros de tamanho/taxa falham cedo e explícitos.

**Piora / pendente:**

- `tempo_s` derivado **assume amostragem uniforme e sem perdas**. Vale para o sample clock
  do DAQmx; se a Fase 2 trouxer timestamp real de hardware, revisar.
- O layout wide não escala para milhares de canais ou arquivos muito longos — aí entra
  TDMS. Para o MVP (poucos canais) está adequado.
- **Só o valor convertido é gravado, não o volt bruto.** Se a auditoria/calibração exigir
  o sinal cru, será preciso uma coluna ou arquivo paralelo (decisão futura).
