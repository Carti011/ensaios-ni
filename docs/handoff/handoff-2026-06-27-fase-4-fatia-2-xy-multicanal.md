# Handoff: Fase 4 fatia 2 — XY + multicanal (empilhamento, XY carga×deformação, seleção)

**Data:** 2026-06-27
**Status:** fatia 2 fechada e commitada na `develop` (**sem push/merge**). 126 testes verdes.
Próximo é a **fatia 3 (aferição na UI)**, idealmente em outro chat.

> **Fonte única do status é o [roadmap.md](../roadmap.md).** Este handoff é o ponto de entrada da
> próxima sessão; o anterior ([fatia 1 — monitor ao vivo](handoff-2026-06-26-fase-4-fatia-1-monitor-ao-vivo.md))
> cobre a base que esta fatia estendeu.

## 1. Objetivo

Construir a **fatia 2** do dashboard (Fase 4, [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md)):
fazer o monitor ao vivo deixar de jogar todos os canais num eixo Y único (onde o `µε` achatava
kgf/bar/mm) e ganhar o gráfico **XY carga×deformação** da prova de carga estática, mais a **seleção
de canais** que o tio espera (à la AqDados). Tudo consumindo o backend já pronto via porta
`FonteDeAquisicao` — o backend **não muda**.

## 2. Contexto essencial

- **Arquitetura da UI (ADR-015):** Presenter `MonitorAoVivo` (Python puro, sem PySide, testável no
  Mac sem display) + Widget PySide6 fino. `import PySide6` **só** em `apresentacao/qt/` (guarda de
  AST). A lógica nova mora no Presenter; o widget só desenha.
- **Decisão de design da fatia 2 ([ADR-016](../adr/016-visualizacao-do-dashboard.md)):** a lógica de
  visualização é **transformação pura** do value object `QuadroAoVivo` (`agrupar_por_unidade`,
  `par_xy`) — testável no Mac, widget burro.
- **Empilhamento por UNIDADE, não por canal:** canais de mesma unidade dividem o sub-plot (mesmo
  eixo Y); unidades distintas em sub-plots separados, eixo X de tempo compartilhado. A causa do
  achatamento é a mistura de escalas.
- **Seleção é SÓ visualização:** o checkbox liga/desliga o traço no sinal×tempo. **Não** afeta a
  gravação do CSV (grava sempre todos os canais) **nem** o gráfico XY. Por isso é estado de UI no
  widget, fora do Presenter.
- **Roda no Mac com o `fake`;** Windows/hardware só na Fase 5. Stack: **PySide6 + pyqtgraph** (extra
  opcional `[gui]`, roda em ARM).
- **Filosofia de produto (inalterada):** usuário é o **tio** (OFM); fluxo/vocabulário espelham o
  AqDados (Lynx); a entrega (UX) a gente melhora.

## 3. O que já foi feito (nesta sessão, TDD red-green-refactor)

**Peça 1 — empilhamento por unidade** (commit `acb8bc7`):
- Presenter: `QuadroAoVivo.agrupar_por_unidade() -> list[GrupoUnidade]` (3 testes em
  `tests/apresentacao/test_quadro.py`: separa unidades distintas, junta as iguais na ordem do
  config, quadro vazio → lista vazia).
- Widget: `_montar_grafico` virou `pg.GraphicsLayoutWidget` com um `PlotItem` por unidade, eixo X
  compartilhado (`setXLink`), rótulo de tempo só no último. Smoke multi-unidade.

**Peça 2 — XY carga×deformação** (commit `e4e21eb`):
- Presenter: `QuadroAoVivo.par_xy(canal_x, canal_y) -> ParXY` (pareia dois canais já alinhados no
  tempo — trivial de propósito; o alinhamento foi feito no `passo()` da fatia 1). 1 teste.
- Widget: painel XY num `QSplitter` ao lado do empilhamento, com `QComboBox` para X e Y; eixos
  rotulados pela unidade. Default X = primeiro canal, Y = último. 1 smoke.

**Tarefa futura registrada** (commit `09adaf6`): **nome do sinal** — ver §5.

**Demo defasada** (commit `3f5ec50`): `aplicacao/demo.py` passou a dar uma frequência levemente
distinta a cada canal, para o XY **evoluir na tela** (antes os sinais eram a mesma senoide em fase →
XY era uma reta fixa, parecia "parado").

**Peça 3 — seleção + recolhimento** (commit `ee9b2b2`):
- Widget: checkbox por canal na tabela (coluna "Canal"); `_visiveis` controla quais traços aparecem.
  Quando **todos** os canais de uma unidade são desmarcados, o sub-plot **recolhe**
  (`_reorganizar_subplots` faz `clear()` + `addItem` reaplicando o `setXLink`). 2 smokes (oculta/
  revela canal; recolhe/volta sub-plot).
- Janela do XY limitada aos **últimos 150 pontos** (`_JANELA_XY`): o laço recente, não o histórico
  acumulado (que virava uma "bola de lã").

**Documentação** (commit `92a5e88`): ADR-016 (Aceito), índice de ADRs, roadmap (fatias 1 e 2 ✅),
CHANGELOG, range `adr/001…016` no CLAUDE.md.

## 4. Estado atual

- **126 testes verdes** no Mac (`uv run pytest`), incl. smoke PySide headless (`offscreen`) e guarda
  de AST. Sem `nidaqmx`.
- **Funciona e foi validado na tela pelo Weslley** (vários screenshots): 4 sub-plots empilhados por
  unidade (kgf/bar/mm/µε), XY vivo (figura de Lissajous na demo defasada), seleção escondendo traços
  e recolhendo sub-plots de 4→2.
- **Working tree limpo** após os 6 commits da sessão (este handoff é o 7º).
- **Fatia 2 = FECHADA.**

## 5. Bloqueios e dependências

- **Push e merge são do Weslley** — todos os commits estão só na `develop` local.
- **Nome do sinal (pendência de UX, NÃO resolvida de propósito):** os seletores X/Y e a tabela
  mostram o **endereço físico** do canal (`Mod1/ai0`), que o tio **não reconhece** — ele pensa por
  nome do sinal ("Carga", "Sg1 bico"), como a coluna "Nome do Sinal" do AqDados. Conserto registrado
  em **[tarefas-futuras.md](../tarefas-futuras.md) §3**: backend (campo `rotulo` no `Canal` + TOML,
  com fallback pro endereço) → depois UI mostra "rótulo — unidade". **Encaixa naturalmente na fatia 3**
  (que já mexe na tabela de canais).
- **Fatia 3 precisa de `tomlkit`** (escrever TOML preservando comentários; o `tomllib` é só leitura).

## 6. Comportamentos deliberados (NÃO são bugs — não "consertar" sem pensar)

- **Iniciar sem nenhum canal marcado** roda e **grava o CSV normalmente** — a seleção é só
  visualização; não se perde dado por esconder traço. (Só não desenha.)
- **Mesmo canal em X e Y** no XY dá a diagonal `y=x` — correto, só sem utilidade. Não é impedido
  (inofensivo); vira refinamento se confundir o tio.
- **XY em forma de reta com dados reais** é o esperado (carga×deformação proporcional = lei de
  Hooke). A figura de Lissajous só aparece na **demo** porque os sinais sintéticos foram defasados de
  propósito para mostrar movimento.

## 7. Próximos passos (fatia 3 — aferição na UI, em OUTRO chat)

1. **Tabela de canais editável** + painel de **aferição** (espelha o "Aferir" do AqDados): tabela de
   pontos `(V, valor eng.)`, **regressão linear**, **correlação %** e **tara**. O domínio já tem tudo
   (`dominio/regressao.py` → `ajustar_regressao`/`Reta`; `dominio/conversao.py`; tara) — a fatia é
   **UI + persistência**, não lógica nova de cálculo.
2. **Persistir no TOML** ao aplicar a aferição: adicionar `tomlkit` (preserva comentários; `tomllib`
   é só leitura). É a primeira vez que a UI **escreve** config.
3. **Nome do sinal** (tarefas-futuras §3) entra aqui: campo `rotulo` no `Canal`/TOML (backend,
   commit separado) → tabela e seletores X/Y mostram "rótulo — unidade".
4. **TDD primeiro no domínio/Presenter** (Python puro, Mac); o widget só desenha. Manter a guarda de
   PySide e o `import nidaqmx` fora de tudo que não seja `daqmx.py`.
5. Depois: fatia 4 (metadata do ensaio + exportar pela UI, reusando os exportadores).

## 8. Artefatos relevantes

- **Decisões:** [ADR-016](../adr/016-visualizacao-do-dashboard.md) (fatia 2),
  [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md) (UX + plano de fatias),
  [referencia-lynx.md](../referencia-lynx.md) (aferição do AqDados, alvo da fatia 3).
- **Código (estenda aqui na fatia 3):**
  - `src/ensaios_ni/apresentacao/monitor.py` — Presenter `MonitorAoVivo` + value objects
    `QuadroAoVivo`/`GrupoUnidade`/`ParXY`.
  - `src/ensaios_ni/apresentacao/qt/janela.py` — Widget PySide6 (tabela, sub-plots, XY, seleção).
  - `src/ensaios_ni/dominio/regressao.py`, `dominio/conversao.py`, `dominio/canais.py` — o que a
    aferição vai usar/estender.
  - Testes: `tests/apresentacao/test_quadro.py`, `test_janela_qt.py`, `test_monitor.py`.
- **Interface de visualização (o que a fatia 2 adicionou):**
  ```python
  quadro = monitor.quadro()                       # QuadroAoVivo(tempos, dados, unidades)
  quadro.agrupar_por_unidade()                    # -> [GrupoUnidade(unidade, dados)]  (empilhamento)
  quadro.par_xy("Mod1/ai0", "Mod3/ai0")           # -> ParXY(canal_x, canal_y, xs, ys)  (XY)
  ```
- **Comandos:**
  - `uv run pytest` → **126 passed** (confirma a base).
  - **Abrir o dashboard (Mac, com tela):** `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.janela`

## 9. Como iniciar a próxima sessão (fatia 3, no Mac)

1. Ler **este handoff** + [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md) (plano de fatias) +
   [ADR-016](../adr/016-visualizacao-do-dashboard.md) + [referencia-lynx.md](../referencia-lynx.md)
   §1.2–1.3 (Aferição por Regressão Linear do AqDados, o alvo).
2. `uv run pytest` → **126 passed**. Se faltar PySide, `uv sync` instala o `[gui]`.
3. Confirmar com o Weslley se ele **deu push/mergeou** a `develop`; sincronizar se preciso.
4. **Atacar a fatia 3 via TDD**, começando pelo domínio/Presenter (Python puro): a aferição reusa
   `ajustar_regressao`/`Reta`/`converter`/tara — a novidade é **UI + escrever o TOML** (`tomlkit`).
   Incluir o **nome do sinal** (tarefas-futuras §3).
5. Regras de sempre: `import nidaqmx` só em `daqmx.py` (lazy); `import PySide6` só em
   `apresentacao/qt/` (guarda de AST); strain nunca usa defaults da API; português em tudo; commits
   separados por camada (backend/aplicação ≠ frontend); **nada de commit/push/merge autônomo**.
