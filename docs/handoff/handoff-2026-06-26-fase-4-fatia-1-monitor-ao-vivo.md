# Handoff: Fase 4 iniciada — ADR-015 (UX) + fatia 1 do dashboard (monitor ao vivo)

**Data:** 2026-06-26
**Status:** aguardando decisão (fatia 1 fechada e commitada na `develop`, **sem push**; próximo é a fatia 2, idealmente em outro chat). 118 testes verdes.

> **Há três handoffs de 2026-06-26.** Os outros dois cobrem o fechamento da Fase 3 (backend) e a
> organização da documentação. **Este é o mais recente** e cobre o início da **Fase 4 (dashboard)**:
> a decisão de UX (ADR-015) e a primeira fatia implementada. A fonte de verdade do status é sempre o
> [roadmap.md](../roadmap.md).

## 1. Objetivo

Construir a **interface gráfica** (Fase 4) que torna o software usável pelo tio (OFM Engenharia) —
o que transforma "funciona no terminal" em "o tio consegue usar" e larga o FlexLogger (pago).
Esta sessão **planejou a UX (discovery)** e **implementou a fatia 1 (monitor ao vivo)**: ver o sinal
correndo na tela, em tempo real, consumindo o backend já pronto via porta `FonteDeAquisicao`.

## 2. Contexto essencial

- **Backend (Fases 0–3) está completo** e isolado atrás da porta `FonteDeAquisicao` (ADR-001):
  `ler_tensao`/`ler_strain` e `transmitir_tensao`/`transmitir_strain`. A UI só **consome**; o
  backend **não muda**. Roda no Mac com o adaptador `fake`; Windows só na Fase 5.
- **Stack do dashboard:** **PySide6 + pyqtgraph** (desktop nativo). O ADR-013 dizia "PyQt6/PySide6";
  esta sessão **fixou PySide6** (LGPL, oficial da Qt) por causa do `.exe` distribuído (Fase 6) —
  PyQt6 é GPL. Ver [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md).
- **Decisão de arquitetura da UI (ADR-015):** separar **Presenter** (Python puro, sem PySide,
  testável no Mac sem display) do **Widget** (PySide6 fino). Espelha a filosofia porta/adaptador:
  assim como `nidaqmx` só vive em `daqmx.py`, **PySide só vive em `apresentacao/qt/`** — travado por
  teste-guarda de AST.
- **Decisões de UX (discovery `/planejar-ux`):** **workspace de painéis** (janela única: canais à
  esquerda, gráfico ao centro, controle no rodapé), visual **moderno-minimalista**, vocabulário do
  Lynx em PT, **decimal vírgula (BR)**.
- **Tema:** mantido **como está** — gráfico claro (pyqtgraph fundo branco) + *chrome* seguindo o
  tema do SO (escuro no macOS do dev, claro no Windows do tio). O Weslley **aprovou na tela**; não
  fixamos QSS claro (registrado no ADR-015).
- **Filosofia de produto (inalterada):** núcleo técnico segue o padrão de mercado; fluxo espelha o
  AqDados (Lynx); entrega (UX) a gente melhora. O usuário é o **tio**, não o Weslley.

## 3. O que já foi feito (nesta sessão)

**Planejamento (docs):**
- Discovery de UX (`/planejar-ux`) → **design brief** completo (ação primária, layout, estados,
  interação, plano de fatias).
- **ADR-015 (Aceito):** UX e fluxo do dashboard + **fixa PySide6**. Refina o ADR-013.
- Índice de ADRs ([docs/adr/README.md](../adr/README.md)) atualizado (linha 015 + fio `013 → 015`);
  nota de remissão no corpo do ADR-013; range `adr/001…015`, regra 6 e árvore no `CLAUDE.md`.

**Fatia 1 — monitor ao vivo (código, TDD, 9 ciclos red-green-refactor):**
- **Presenter** `src/ensaios_ni/apresentacao/monitor.py` (`MonitorAoVivo`, `EstadoMonitor`,
  `QuadroAoVivo`) — Python puro, **8 testes**: consome `transmitir_*` da porta, converte cada bloco
  (`dominio.conversao.converter`), mantém **ring buffer** (`deque(maxlen=)` — janela deslizante p/
  ensaios longos) com **tempo absoluto**, expõe `quadro()` (tempos + valor/canal) e `valor_atual`,
  grava CSV via `GravadorEnsaioCsv`. Máquina de estados **PARADO/ADQUIRINDO/ERRO**: fonte esgotada
  **para limpo**; erro de aquisição vira estado **ERRO sem traceback**. **Reinício zera tempo e
  limpa a janela** (cada Iniciar = ensaio novo; corrigido após o print do Weslley mostrar o eixo
  acumulando entre cliques).
- **Widget** `src/ensaios_ni/apresentacao/qt/janela.py` (`JanelaMonitor`) — PySide6 + pyqtgraph,
  casca fina ligada por `QTimer → passo()`: tabela de canais (nome/unidade/valor ao vivo) + gráfico
  sinal×tempo + barra Iniciar/Parar + label de estado. Função `abrir()` e `_monitor_demonstracao()`
  (fake + `canais.exemplo.toml`) para rodar no Mac. **1 smoke test** headless (`offscreen`).
- **Teste-guarda** `tests/arquitetura/test_regra_pyside.py` (**3 testes**): trava `import PySide6`
  fora de `apresentacao/qt/` (AST), com detector positivo/negativo.
- `pyproject.toml`: extra opcional **`[gui]`** = `PySide6>=6.6` + `pyqtgraph>=0.13`; ambos também no
  grupo `dev` (rodam em ARM). `uv.lock` atualizado.

**Git:** 2 commits na `develop` (sem push):
- `0163c38 docs(adr): ADR-015 — UX e fluxo do dashboard, fixa PySide6`
- `eef7450 feat(apresentacao): monitor ao vivo do dashboard (Fase 4, fatia 1)`

## 4. Estado atual

- **118 testes verdes** no Mac (`uv run pytest`), incluindo o smoke PySide headless e a guarda de
  AST. Sem `nidaqmx`. ~12 s na primeira vez (instala o `[gui]`), <1 s depois.
- **Funciona:** a janela abre, **Iniciar** roda o sinal sintético dos 5 canais do
  `canais.exemplo.toml` ao vivo (sinal×tempo), atualiza a tabela, grava CSV, e **Parar**/esgotar
  encerram limpo. Validado na tela pelo Weslley (dois screenshots).
- **Working tree limpo** após os 2 commits (este handoff é o 3º commit).
- **Fatia 1 = FECHADA.**

## 5. Bloqueios e dependências

- **Push e merge são do Weslley** — os 2 commits estão só na `develop` local.
- **Limitação de visualização conhecida (alvo da fatia 2):** todos os canais são plotados num
  **eixo Y único**. O `Mod3/ai0` (µε, ±1000) **domina e achata** os demais (kgf/bar/mm, dezenas).
  Misturar unidades numa escala só esconde sinal — o AqDados resolve **empilhando um gráfico por
  canal**. É o coração da fatia 2.
- **Demo do Mac encerra sozinha** porque o `fake` tem amostras finitas (5000 @ 100 Hz ≈ 50 s). No
  hardware real / `daqmx` contínuo o fluxo é **infinito** (só para por comando) — comportamento
  esperado, não é bug.
- **Número físico do strain / TXT-AqAnalysis:** seguem pendentes (Fase 5). Não bloqueiam a fatia 2.

## 6. Próximos passos (fatia 2 — em OUTRO chat)

1. **Empilhamento por canal/unidade** no gráfico: um sub-plot por canal (ou agrupar por unidade),
   para o µε parar de engolir kgf/bar/mm. Espelha o AqDados (gráficos empilhados). Eixo X de tempo
   compartilhado.
2. **XY carga × deformação** (estático): escolher canal X e canal Y, plotar um contra o outro — o
   "XY Graph" do FlexLogger / requisito do ensaio de prova de carga.
3. **Seleção de canais a exibir** (checkbox na tabela, à la AqDados) — exibir só o que interessa.
4. **TDD primeiro no Presenter** (Python puro): a lógica de "agrupar séries por unidade" e "montar o
   par XY" mora no Presenter e é testável no Mac; o Widget só desenha. Manter a guarda de PySide.
5. Depois: fatia 3 (aferição na UI — pontos/regressão/correlação/tara, escrevendo o TOML; precisa de
   `tomlkit`, o `tomllib` é só leitura) e fatia 4 (metadata + exportar pela UI, reusando os
   exportadores).

## 7. Artefatos relevantes

- **Decisão/UX:** [docs/adr/015-ux-e-fluxo-do-dashboard.md](../adr/015-ux-e-fluxo-do-dashboard.md)
  (brief completo, layout, estados, plano de fatias), [docs/adr/013](../adr/013-stack-do-dashboard.md)
  (stack), [docs/referencia-lynx.md](../referencia-lynx.md) (UX do AqDados a espelhar).
- **Código da fatia 1:**
  - `src/ensaios_ni/apresentacao/monitor.py` — Presenter (a lógica; estenda aqui na fatia 2).
  - `src/ensaios_ni/apresentacao/qt/janela.py` — Widget PySide6 (só desenho).
  - `tests/apresentacao/test_monitor.py` (9 testes), `tests/apresentacao/test_janela_qt.py` (smoke),
    `tests/arquitetura/test_regra_pyside.py` (guarda).
- **Interface do Presenter (o que a fatia 2 vai estender):**
  ```python
  monitor = MonitorAoVivo(fonte, canais, taxa_hz, amostras_por_bloco, caminho, capacidade_janela=None)
  monitor.estado            # EstadoMonitor.PARADO | ADQUIRINDO | ERRO
  monitor.iniciar()         # abre fluxos + GravadorEnsaioCsv; zera tempo e janela
  monitor.passo() -> bool   # consome 1 bloco/fluxo, converte, grava, alimenta o ring buffer
  monitor.parar()
  monitor.quadro()          # QuadroAoVivo(tempos: list, dados: dict[str,list], unidades: dict)
  monitor.valor_atual(canal)
  ```
- **Comandos:**
  - `uv run pytest` → **118 passed**.
  - **Abrir o dashboard (Mac, com tela):** `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.janela`
  - Smoke headless já roda no pytest via `QT_QPA_PLATFORM=offscreen`.

## 8. Como iniciar a próxima sessão (fatia 2, no Mac)

1. Ler **este handoff** + [docs/adr/015-ux-e-fluxo-do-dashboard.md](../adr/015-ux-e-fluxo-do-dashboard.md)
   + [docs/referencia-lynx.md](../referencia-lynx.md) (gráficos empilhados, XY carga×deformação).
2. `uv run pytest` → **118 passed** (confirma a base). Se faltar PySide, `uv sync` instala o `[gui]`.
3. Confirmar com o Weslley se ele **deu push / mergeou** a `develop`; sincronizar se preciso.
4. **Atacar a fatia 2 via TDD**, começando pelo **Presenter** (Python puro): agrupar séries por
   unidade (empilhamento) e montar o par XY — testes no Mac, sem display. Só depois o Widget desenha
   (sub-plots pyqtgraph + plot XY).
5. Regras de sempre: `import nidaqmx` só no `daqmx.py` (lazy); **`import PySide6` só em
   `apresentacao/qt/`** (guarda de AST); strain nunca usa defaults da API; português em tudo;
   commits separados por camada; **nada de commit/push/merge autônomo**.
