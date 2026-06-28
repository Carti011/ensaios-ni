# Handoff: Fase 4 fechada — metadata + exportar + tara ao vivo (fatia 4) e correções

**Data:** 2026-06-28
**Status:** **Fase 4 (dashboard) concluída.** 9 commits na `develop`, 178 testes verdes. Validado na
tela pelo Weslley. Push e **PR `develop → main`** feitos nesta sessão; **merge é do Weslley**.

> **Fonte única do status é o [roadmap.md](../roadmap.md)** (Fase 4 ✅; faltam 5 e 6). Este handoff é
> o ponto de entrada da próxima sessão; o anterior
> ([fatia 3 — aferição na UI](handoff-2026-06-27-fase-4-fatia-3-afericao-na-ui.md)) cobre a base que
> esta fatia estendeu.

## 1. Objetivo

Fechar a **Fase 4 (dashboard)** implementando a **fatia 4** ([ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md)
§plano de fatias): **metadata do ensaio**, **exportar pela UI** e **tara ao vivo**. No caminho,
corrigir dois problemas que o Weslley pegou validando na tela (a calibração aferida não entrava no
gráfico; o divisor entre os gráficos era invisível).

## 2. Contexto essencial

- **Arquitetura da UI (ADR-015):** Presenter (Python puro, testável no Mac sem display) + Widget
  PySide6 fino. `import PySide6` **só** em `apresentacao/qt/`; `import nidaqmx` só em `daqmx.py`;
  `import openpyxl` lazy. Todas as guardas de AST seguem verdes.
- **Filosofia de produto (inalterada):** usuário é o **tio** (OFM); núcleo técnico segue o padrão
  (Zero Channel, regressão); fluxo/vocabulário espelham o Lynx (AqDados/AqDAnalysis); a entrega (UX)
  a gente melhora.
- **Decisão desta fatia ([ADR-018](../adr/018-metadata-do-ensaio.md)):** a metadata do ensaio
  (obra/operador/data/observação) vive num **arquivo paralelo `<ensaio>.meta.toml`** ao lado do CSV
  — o CSV continua só dados (layout "wide", ADR-003), e o `carregar_csv` fica intacto. Os
  exportadores **carimbam** a metadata no cabeçalho do laudo; o `txt-aqanalysis` fica de fora (layout
  de importação sensível/provisório).
- **Semântica da calibração (decidida com o Weslley):** aferir é **etapa pré-ensaio**; a calibração
  fica **fixa durante a aquisição** (rastreabilidade do laudo) e a nova vale **do próximo Iniciar**.
- **Semântica da tara:** **Zero Channel** — com a peça em repouso, o próximo bloco vira o zero; é
  **por-ensaio** (cada Iniciar recomeça sem zero).

## 3. O que já foi feito (cronológico, TDD red-green-refactor)

1. **`fix(apresentacao)` `5ea5554` — recarregar calibração após aferir.** Bug: ao aplicar uma
   aferição, o `canais.toml` era reescrito, mas o `MonitorAoVivo` seguia com os `Canal` antigos em
   memória → o gráfico não mudava. Correção: `MonitorAoVivo.recarregar_canais(canais)` (recusa
   durante a aquisição via `AquisicaoEmAndamento`); ao **Aplicar**, a janela relê o TOML e injeta no
   monitor; botão **Aferir** desabilitado enquanto adquirindo.
2. **`feat(apresentacao)` `aaede7a` — divisor visível.** A alça do `QSplitter` entre sinal×tempo e
   XY ganhou largura (10 px) e destaque (acende no acento `#0a9edc` no hover) — o redimensionamento
   estava escondido.
3. **`feat(apresentacao)` `39de6b5` — tara ao vivo (Zero Channel).** `MonitorAoVivo.zerar()` captura
   o próximo bloco de repouso como zero e o subtrai dos canais (reusa `dominio.conversao.calcular_tara`);
   por-ensaio. Botão **Zerar** no rodapé, habilitado só durante a aquisição.
4. **`feat(apresentacao)` `a460f73` — exportar pela UI.** Presenter `Exportacao` (carrega o CSV
   gravado e chama o exportador; espelha a CLI) + `PainelExportacao` (QDialog: formato, seleção de
   sinais, janela de tempo, `QFileDialog`). Botão **Exportar…** habilitado só com ensaio **gravado
   nesta sessão** (`MonitorAoVivo.tem_ensaio`) — **não** por um CSV residual em disco (bug pego pelo
   Weslley: o botão acendia por causa do `ensaio-dashboard.csv` de uma execução anterior).
5. **Metadata (ADR-018)**, em 3 commits backend→frontend:
   - **`feat(dominio)` `c3aa6c4`** — value object `Metadata` + `persistencia/metadata_ensaio.py`
     (`gravar_metadata`/`ler_metadata` no `<ensaio>.meta.toml`; ler ausente devolve `Metadata()`).
   - **`feat(persistencia)` `d7287ea`** — `csv-excel-br` e `xlsx` carimbam a metadata no topo do
     laudo (helper `itens_metadata`); `txt-aqanalysis` aceita o parâmetro mas ignora; a CLI repassa
     a metadata do `.meta.toml` ao reexportar.
   - **`feat(apresentacao)` `f5e987b`** — campos de metadata no topo do dashboard (obra/operador/
     data[hoje]/obs.); ao **Parar** (ou esgotar) um ensaio gravado, salva o `.meta.toml`; o Presenter
     `Exportacao` lê o `.meta.toml` e carimba no export.
6. **`chore` `c0b9140`** — `.gitignore` passou a ignorar `*.xlsx` (exports da UI); exports de teste
   apagados da raiz (`ensaio.xlsx`, `ensaio1.xlsx`, `ensaio2.csv`).
7. **`docs` `c15c9b6`** — ADR-018, índice de ADRs (linha 018 + fio `013→…→018`), roadmap (Fase 4 ✅,
   resumo executivo), CHANGELOG, CONTEXT (termo "Metadata do ensaio"), CLAUDE.md (range `adr/001…018`,
   árvore, status da apresentação).

## 4. Estado atual

- **178 testes verdes** no Mac (`uv run pytest`), incl. smoke PySide headless (`offscreen`) e guardas
  de AST (`nidaqmx`/`PySide6`/`openpyxl`). Sem `nidaqmx`.
- **Validado na tela pelo Weslley** (vários screenshots): calibração aferida agora muda a escala;
  divisor visível; tara recentralizando o sinal; exportar com formato/sinais/janela (conferidos os
  arquivos `ensaio1.xlsx` com janela 1–3 s e `ensaio2.csv` em csv-excel-br com janela 1–5 s); metadata.
- **Dashboard completo** roda no Mac com o `fake`. **Working tree limpo.**
- **Fase 4 = FECHADA.** Próximo é a validação física (Fase 5).

## 5. Bloqueios e dependências

- **Merge `develop → main` é do Weslley** — a PR foi aberta nesta sessão; ele faz o merge.
- **Pendências de Fase 5 (hardware do tio), não bloqueiam o dashboard:** número físico do strain;
  validar o **TXT-AqAnalysis** importando no AqDAnalysis dele; sincronização start-trigger
  tensão/strain (só Windows). Ver [tarefas-futuras.md](../tarefas-futuras.md).
- **Comportamento deliberado (não é bug):** ao zerar no meio de um sinal grande (demo), o gráfico
  "reacomoda" por uns segundos (janela deslizante + auto-range) — no hardware real, zerando com a
  peça em repouso, é suave.

## 6. Próximos passos

1. **Fase 5 — validação física no hardware do tio** (a frente natural; exige o Windows + hardware,
   não dá no Mac): trocar nomes simulados pelos reais no `canais.toml`, bater a leitura com o **test
   panel do NI-MAX**, **calibrar a extensometria** de verdade (número físico do strain), validar o
   **TXT** no AqDAnalysis dele, e rodar o fluxo completo num ensaio de teste. Runbook em
   [validacao-windows.md](../validacao-windows.md).
2. **Fase 6 — empacotamento & adoção:** `.exe` (PyInstaller) para o tio instalar sem `pip`; robustez
   de longa duração (recuperação de queda de rede, rotação de arquivo); polimento de mensagens.
3. **Refinamentos de UI opcionais (no Mac, se quiser antes da Fase 5):**
   - **Alerta de correlação baixa na aferição** — hoje o Aplicar fica liberado mesmo com correlação
     ruim (ex.: 6%); pintar/avisar abaixo de um limiar (pendência ADR-006/017).
   - **Tara: limpar a janela ao zerar** — recomeçar o traço do ponto do zero (some o "reacomodar").
   - **"Ganho e Ponto de Referência"** (2º modo de aferição do AqDados, ADR-006 pendente).

## 7. Artefatos relevantes

- **Decisões:** [ADR-018](../adr/018-metadata-do-ensaio.md) (metadata),
  [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md) (UX/fatias),
  [ADR-006](../adr/006-calibracao-por-pontos.md) (tara/regressão),
  [ADR-011](../adr/011-estrategia-de-exportacao.md)/[ADR-012](../adr/012-serie-temporal-e-exportadores.md)
  (exportadores).
- **Código (Presenters puros, estenda aqui):**
  - `src/ensaios_ni/apresentacao/monitor.py` — `MonitorAoVivo` (ganhou `zerar`, `recarregar_canais`,
    `tem_ensaio`, `caminho`).
  - `src/ensaios_ni/apresentacao/exportacao.py` — Presenter `Exportacao`.
  - `src/ensaios_ni/apresentacao/qt/janela.py` — `JanelaMonitor` + `PainelAfericao` + `PainelExportacao`.
  - `src/ensaios_ni/dominio/metadata.py` + `src/ensaios_ni/persistencia/metadata_ensaio.py`.
- **Interface nova desta sessão:**
  ```python
  monitor.recarregar_canais(canais)   # troca a calibração; recusa adquirindo (AquisicaoEmAndamento)
  monitor.zerar()                     # tara (Zero Channel): próximo bloco de repouso vira o zero
  monitor.tem_ensaio                  # gravou nesta sessão? (habilita o exportar)
  monitor.caminho                     # CSV gravado (origem da exportação)

  Exportacao(caminho_csv).exportar(formato, destino, sinais=None, inicio_s=None, fim_s=None)
  Metadata(obra="", operador="", data="", observacao="")
  gravar_metadata(caminho_csv, metadata) / ler_metadata(caminho_csv)  # <ensaio>.meta.toml ao lado
  ```
- **Comandos:**
  - `uv run pytest` → **178 passed**.
  - **Abrir o dashboard (Mac):** `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.janela`
  - A demo escreve a config de trabalho e o CSV/`.meta.toml` em `$TMPDIR/` (nunca no versionado).

## 8. Como iniciar a próxima sessão

1. Confirmar com o Weslley se a **PR `develop → main` foi mergeada**; se sim, sincronizar a `develop`.
2. Ler **este handoff** + [roadmap.md](../roadmap.md). Para a Fase 5, ler também
   [validacao-windows.md](../validacao-windows.md) e [contexto-hardware.md](../contexto-hardware.md)
   (API pinada do `nidaqmx`, armadilha do strain).
3. `uv run pytest` → **178 passed** (confirma a base). Se faltar PySide, `uv sync` instala o `[gui]`.
4. **Decidir a frente:** Fase 5 exige o **Windows + hardware do tio** (fora do Mac). Se for ficar no
   Mac, atacar um refinamento de UI da §6.
5. Regras de sempre: `import nidaqmx` só em `daqmx.py` (lazy); `import PySide6` só em
   `apresentacao/qt/`; strain nunca usa os defaults da API; português em tudo (textos de UI também);
   commits separados por camada; **nada de commit/push/merge autônomo**.
