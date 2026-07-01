# Handoff: launcher de hardware, tela inicial sem CLI e captura de leitura ao vivo na aferição

**Data:** 2026-07-01  
**Status:** em andamento — três frentes da Fase 5 fechadas no Mac; push e PR `develop → main` feitos nesta sessão (merge é do Weslley). Próximo é escolher entre refinamentos no Mac ou o `.exe` (Windows).

> **Fonte única do status é o [roadmap.md](../roadmap.md).** Este handoff é o ponto de entrada da próxima sessão; o anterior ([gage factor por canal + validação física](handoff-2026-06-30-gage-factor-por-canal-e-validacao-fisica.md)) cobre a base que esta sessão estendeu.

## 1. Objetivo

Substituir o **FlexLogger** (única peça paga da pilha NI) por software próprio em Python sobre o **NI-DAQmx** (gratuito), para o tio (OFM Engenharia: cDAQ-9184 + 2× 9205 de tensão + 1× 9235 de strain). **Critério de sucesso: o tio largar o FlexLogger.** Esta sessão avançou a Fase 5 (adoção) fechando três frentes 100% testáveis no Mac: dar ao tio um jeito de **abrir o dashboard no hardware sem CLI** e **calibrar capturando a tensão ao vivo** (o fluxo real dele no AqDados).

## 2. Contexto essencial

- **Stack:** Python 3.12, `pytest`, `uv` (Mac). `nidaqmx` extra `[hardware]` (só Windows/Linux x86); `PySide6`+`pyqtgraph` extra `[gui]` (roda em ARM); `openpyxl` extra `[excel]`; `tomlkit` dep core. **~90% testável no Mac** com o adaptador `fake`.
- **Arquitetura porta/adaptador ([ADR-001](../adr/001-arquitetura-porta-adaptador.md)):** tudo depende da porta `FonteDeAquisicao`; `import nidaqmx` **só** em `aquisicao/daqmx.py` (lazy); `import PySide6` **só** em `apresentacao/qt/`. Guardas de AST travam o resto.
- **Presenter puro + Widget fino ([ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md)):** a lógica vive em Presenters Python puros (`apresentacao/monitor.py`, `apresentacao/afericao.py`), testáveis no Mac sem display; o widget PySide (`apresentacao/qt/janela.py`) só desenha.
- **Filosofia de produto (inalterada):** núcleo técnico segue o padrão; fluxo/vocabulário espelham o AqDados (Lynx); a entrega (UX) a gente melhora. Usuário é o **tio**, não o Weslley.
- **Armadilha do strain:** defaults da API são full-bridge 350 Ω / 2,5 V; o 9235 é quarter-bridge 120 Ω / 2,0 V — errar dá número plausível e errado sem erro. Travada por teste-guarda.
- **Decisão desta sessão (entrypoint do dashboard de hardware):** módulo novo `qt/hardware.py`, separado da demo `qt/janela.py`. Motivo: separar o programa real da demo `fake` e ser o alvo natural do `.exe` (Fase 6), sem inchar o `__main__.py` (CLI headless).

## 3. O que já foi feito (nesta sessão, TDD red-green-refactor)

Cronológico, com os commits na `develop`:

1. **`fa87f55` feat(apresentacao) — launcher do dashboard com hardware real.** Novo `apresentacao/qt/hardware.py`: `montar_janela(config, taxa, bloco, saida, capacidade_janela)` costura `carregar_canais → AdaptadorDaqmx(canais) → MonitorAoVivo → JanelaMonitor(monitor, canais, config)`. **Repassar canais + config é o miolo** — sem isso, no hardware o Aferir e os rótulos (Nome do Sinal) não funcionariam (o `abrir(monitor)` da demo não passava). `89052c1` docs.
2. **`25569d8` feat(apresentacao) — tela inicial de abertura sem CLI.** `TelaInicial` (widget em `qt/hardware.py`): sem `--config`, abre com o botão **"Abrir configuração…"** → escolhe o `canais.toml` → monta o dashboard. Config inválido → aviso **na própria tela**, sem traceback. `--config` virou **opcional** (com ele, atalho direto). Implementa o estado "Sem config" do [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md) — sem ADR novo. `0ce5055` docs.
   - **Bug real pego ao rodar o entrypoint de verdade** (`QWidget: Must construct a QApplication before a QWidget`, SIGABRT): o `main` construía o widget **antes** do `QApplication`. Os testes headless não pegavam (a fixture `app` já criava o `QApplication`). **Corrigido** extraindo `_preparar(argv)` (cria o `QApplication` antes do widget) + **teste de regressão que roda num processo NOVO** via `subprocess` (`test_entrypoint_cria_qapplication_antes_do_widget`) — único jeito de reproduzir. Incluído no mesmo commit da feature.
3. **`bf21f61` feat(apresentacao) — captura da leitura de tensão ao vivo na aferição** (o "Leitura do A/D" do AqDados, **pedido direto do tio em 30/06**). `MonitorAoVivo.ler_tensao_atual(canal, amostras=100)` lê a tensão **crua** da fonte (média, **sem converter** — a aferição mapeia volts→unidade); `Afericao` recebe a leitura por **callable injetada** (`capturar_tensao()`/`pode_capturar`); `PainelAfericao` ganhou o botão **"Capturar tensão"** que insere a tensão lida e deixa o valor de engenharia em branco pro operador digitar a carga. Injetado **só em canais de tensão** (`JanelaMonitor._abrir_afericao`); strain fica de fora. `5b262d5` docs.

**Validado na tela pelo Weslley:** a tela inicial abriu, escolheu o `config/canais.exemplo.toml`, o dashboard montou; a captura pegou a tensão sintética. (Iniciar dá "erro: No module named 'nidaqmx'" no Mac — **esperado**, o driver só existe no Windows.)

**Cuidado aprendido:** no launcher de hardware o config é o arquivo **real** — aferir/aplicar **escreve nele**. Testar aferição usando o `canais.exemplo.toml` versionado **suja o repo** (aconteceu e foi revertido). A demo `qt.janela` já copia pra um tmp; o `qt.hardware` não, de propósito.

## 4. Estado atual

- **203 testes verdes** no Mac (`uv run pytest`), incl. smokes PySide headless, guardas de AST e o teste de regressão do entrypoint em subprocess. Sem `nidaqmx`.
- **Funciona:** ciclo ler → calibrar (com captura ao vivo) → gravar → exportar, pela CLI e pelo dashboard, no Mac com o `fake`; a leitura real do 9235 responde à deformação no hardware do tio (29/06).
- **Working tree limpo.** Branch `develop`, **8 commits à frente da `main`** (os 6 desta sessão + `69c0451`/`e2c00de` de 30/06 sobre gage factor por canal / ADR-020, que ainda não estavam na `main`), mais o commit deste handoff.
- **Fase 5:** funcional feita; faltam os ajustes finos que dependem do tio (ver §5/§6).

## 5. Bloqueios e dependências

- **Merge `develop → main` é do Weslley** — a PR foi aberta nesta sessão; ele revisa e faz o merge.
- **Ajustes finos da Fase 5 dependem do hardware/Windows do tio:** comparação numérica com o test panel do NI-MAX (por **variação** carregado−repouso, mesma unidade) e validar o **TXT** no AqDAnalysis dele. Fora do Mac.
- **`.exe` (Fase 6):** o build/teste do binário só roda no Windows; no Mac dá pra preparar o `.spec` e o guia, mas não validar de verdade.
- Nenhum bloqueio de código no Mac para as frentes de refinamento (§6).

## 6. Próximos passos

**Testáveis no Mac (rápidos, alto valor — recomendados para a próxima sessão):**

1. **Alerta de correlação baixa na aferição** (🟠, [tarefas-futuras.md](../tarefas-futuras.md)) — hoje **Aplicar** libera mesmo com correlação ruim (ex.: 6%). Pintar/avisar abaixo de um limiar (risco metrológico no laudo). Mexe em `Afericao.correlacao_percentual`/`PainelAfericao._sincronizar`. Par natural da captura recém-feita — fecha o fluxo de aferição com segurança.
2. **Mensagens de erro amigáveis na aquisição** (registrado em [tarefas-futuras.md](../tarefas-futuras.md)) — o `MonitorAoVivo.passo()` mostra `str(erro)` cru no rótulo de estado (ex.: `No module named 'nidaqmx'` no Mac; falha de chassi/rede no Windows). Traduzir para texto que o tio entenda. Polimento previsto na Fase 6 do roadmap.

**Dependem do Windows/hardware do tio:**

3. **`.exe` (Fase 6, PyInstaller):** preparar `.spec` (entrypoint = `qt.hardware.main`, incluir PySide6/pyqtgraph/tomlkit/nidaqmx) no Mac; gerar e testar o binário no Windows.
4. **Validação numérica no tio:** comparar a variação carregado−repouso NI-MAX × software; importar o TXT no AqDAnalysis. Roteiro em [guia-teste-hardware.md](../guia-teste-hardware.md).

**Sem prazo (precisam de decisão/ADR):** FFT ao vivo (paridade dinâmica — precisa de ADR-árbitro); sincronização start-trigger tensão×strain (só Windows); robustez de longa duração (rotação de arquivo, recuperação de rede).

## 7. Artefatos relevantes

- **Código novo/tocado:**
  - `src/ensaios_ni/apresentacao/qt/hardware.py` — launcher + `TelaInicial` + `_preparar`/`_widget_de`/`main`.
  - `src/ensaios_ni/apresentacao/monitor.py` — `MonitorAoVivo.ler_tensao_atual`.
  - `src/ensaios_ni/apresentacao/afericao.py` — `Afericao(capturar=…)`, `capturar_tensao`, `pode_capturar`.
  - `src/ensaios_ni/apresentacao/qt/janela.py` — `_abrir_afericao` injeta a captura (só tensão); `PainelAfericao` botão "Capturar tensão".
  - Testes: `tests/apresentacao/test_hardware.py`, `test_monitor.py`, `test_afericao.py`, `test_janela_qt.py`.
- **Interfaces novas:**
  ```python
  # launcher de hardware
  montar_janela(config, taxa_hz, bloco, saida, capacidade_janela=None) -> JanelaMonitor
  TelaInicial(taxa_hz=1024.0, bloco=256, saida=Path("ensaio.csv"), capacidade_janela=2000)
  TelaInicial.abrir_config(caminho) -> JanelaMonitor | None   # config inválido -> None + aviso na tela

  # captura de leitura ao vivo
  MonitorAoVivo.ler_tensao_atual(canal, amostras=100) -> float   # tensão crua, sem converter
  Afericao(caminho, canal, pontos, capturar=Callable[[], float] | None)
  Afericao.capturar_tensao() -> float | None
  Afericao.pode_capturar -> bool
  ```
- **Comandos:**
  - `uv run pytest -q` → **203 passed**.
  - Demo `fake` (Mac, aferição na cópia de trabalho): `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.janela`
  - Dashboard de hardware (Windows): `python -m ensaios_ni.apresentacao.qt.hardware` (tela inicial) ou `... --config config/canais.toml --taxa 1024 --bloco 256` (direto).
- **Decisões:** [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md) (UX/estado "Sem config"), [ADR-017](../adr/017-afericao-na-ui-e-escrita-de-config.md) (aferição na UI — a captura o refina), [ADR-001](../adr/001-arquitetura-porta-adaptador.md) (isolamento do driver).

## 8. Como iniciar a próxima sessão

1. Ler **este handoff** + [roadmap.md](../roadmap.md) (status). Não precisa reler todos os ADRs.
2. `uv run pytest -q` → **203 passed** (confirma a base). Se faltar PySide, `uv sync` instala o `[gui]`.
3. Confirmar com o Weslley se a **PR `develop → main` foi mergeada**; se sim, sincronizar a `develop`.
4. **Decidir a frente:** no Mac, começar pelo **alerta de correlação baixa** (§6.1, TDD no Presenter `Afericao` + smoke no `PainelAfericao`); no Windows, preparar o **`.exe`** ou validar no tio.
5. Regras de sempre: `import nidaqmx` só em `daqmx.py` (lazy); `import PySide6` só em `apresentacao/qt/`; strain nunca usa os defaults da API; português em tudo (textos de UI também); commits separados por camada; **nada de commit/push/merge autônomo**.
