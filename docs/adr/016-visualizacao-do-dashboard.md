# ADR 016 — Visualização do dashboard: empilhamento, XY e seleção (Fase 4, fatia 2)

## Status

**Aceito** (27/06/2026). Implementa a **fatia 2** do plano de fatias do
[ADR-015](015-ux-e-fluxo-do-dashboard.md) ("XY + multicanal"). Não altera a arquitetura decidida
ali (Presenter Python puro + Widget PySide6 fino); registra as **decisões de design da
visualização** tomadas durante a implementação, para o futuro-eu entender o porquê.

## Contexto

A fatia 1 (monitor ao vivo, ADR-015) plotava todos os canais num **eixo Y único**. Na prática o
canal de strain (`µε`, faixa ±1000) **achatava** os demais (kgf/bar/mm, dezenas) — misturar
unidades numa escala só esconde sinal. O AqDados (Lynx) resolve **empilhando um gráfico por
canal/unidade** (ver [referencia-lynx.md](../referencia-lynx.md) §2.1). Além disso, a prova de
carga estática precisa do gráfico **carga × deformação** (o "XY Graph" do FlexLogger), e o tio
precisa **escolher quais canais ver** (checkbox, à la AqDados).

O backend não muda: a UI só consome `quadro()` do Presenter `MonitorAoVivo` (ADR-001/015).

## Decisão

### 1. Empilhamento por **unidade**, não por canal

Canais de **mesma unidade** compartilham um sub-plot (mesmo eixo Y); **unidades distintas** ganham
sub-plots separados, com **eixo X de tempo compartilhado**. A chave é a unidade porque a causa do
achatamento é a mistura de escalas — agrupar por unidade dá a cada grandeza sua própria escala e
ainda deixa canais comparáveis (ex.: dois `mm`) juntos.

### 2. Lógica de visualização como **transformação pura** do `QuadroAoVivo`

`agrupar_por_unidade() -> list[GrupoUnidade]` e `par_xy(canal_x, canal_y) -> ParXY` vivem no
**value object** `QuadroAoVivo` (Python puro), não no widget. São testáveis no Mac sem display
(red-green-refactor), e o widget só **desenha** o resultado. Espelha a filosofia porta/adaptador e
a separação Presenter/Widget do ADR-015: a complexidade fica onde dá para testar.

O par XY é trivial **de propósito** — o trabalho pesado (manter as séries alinhadas no tempo, mesmo
sample clock) já foi feito no `passo()` da fatia 1; o ponto `i` de cada canal é simultâneo.

### 3. Seleção de canais é **só visualização**

O checkbox por canal liga/desliga o **traço no gráfico sinal×tempo**. **Não** afeta a **gravação do
CSV** (todos os canais são sempre gravados — não se perde dado por esconder um traço) **nem o
gráfico XY** (que tem seus próprios seletores X/Y). Por isso é estado de UI no widget, fora do
Presenter e do `quadro()`. Consequência aceita: dá para **Iniciar sem nenhum canal marcado** — o
ensaio roda e grava normalmente, só não desenha.

### 4. Recolhimento do sub-plot vazio

Quando **todos** os canais de uma unidade são desmarcados, o sub-plot daquela unidade **recolhe**
(o layout é reorganizado e os demais ocupam o espaço), em vez de deixar um eixo órfão sem traço.
Reorganiza via `clear()` + `addItem` reaplicando o `setXLink`.

### 5. Janela do gráfico XY limitada aos últimos N pontos

O XY mostra só o **laço recente** (hoje `_JANELA_XY = 150` pontos), não o histórico inteiro
acumulado — que, num ensaio longo, vira um emaranhado ilegível. O sinal×tempo continua com a janela
deslizante cheia (ring buffer do Presenter).

## Consequências

- **Backend intacto.** Só o value object `QuadroAoVivo` ganhou `GrupoUnidade`, `ParXY`,
  `agrupar_por_unidade` e `par_xy` (transformações puras). Domínio/persistência/aquisição não mudam.
- **126 testes verdes** no Mac, sem `nidaqmx` nem display (smoke PySide headless + guarda de AST).
- **Pendência registrada** (não bloqueia): os seletores X/Y e a tabela mostram o **endereço físico**
  do canal (`Mod1/ai0`), que o tio não reconhece — ele pensa por **nome do sinal** ("Carga", "Sg1
  bico"), como na coluna "Nome do Sinal" do AqDados. Conserto (campo `rotulo` no `Canal` + UI) está
  em [tarefas-futuras.md](../tarefas-futuras.md) §3.
- **Nota de comportamento:** escolher o **mesmo canal** em X e Y no XY dá a diagonal `y=x` — correto,
  mas sem utilidade. Não é impedido (inofensivo); pode virar refinamento se confundir o tio.
- **Demonstração:** o gerador de sinal sintético da demo passou a usar **frequências levemente
  distintas por canal** para o XY evoluir na tela (só `aplicacao/demo.py`; com dados reais o XY se
  move sozinho).
- **Próximo:** fatia 3 (aferição na UI — pontos/regressão/correlação/tara, escrevendo o TOML).
