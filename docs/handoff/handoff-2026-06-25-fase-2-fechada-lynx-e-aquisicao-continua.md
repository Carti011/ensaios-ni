# Handoff: Fase 2 fechada — virada de norte para o Lynx e aquisição contínua

**Data:** 2026-06-25
**Status:** aguardando decisão (PR #4 develop→main aberta — o Weslley faz o merge no GitHub). Fase 2 (backend) **completa e validada no Windows simulado**. Próximo é a Fase 3, em **outro chat**.

## 1. Objetivo

Substituir LabVIEW/FlexLogger (pagos) por software próprio em Python sobre o driver gratuito NI-DAQmx, para o hardware do tio do Weslley (OFM Engenharia: cDAQ-9184 + 2× NI 9205 de tensão + 1× NI 9235 de strain). Esta sessão (1) absorveu os prints dos softwares que o tio realmente usa e **mudou o norte de paridade**, (2) **integrou tensão+strain** num mesmo ensaio, (3) implementou a **aquisição contínua** de longa duração e (4) **fechou a Fase 2** validando no Windows.

## 2. Contexto essencial

- **Stack:** Python 3.12, `pytest`, `uv` (Mac). `nidaqmx` é extra opcional `[hardware]`, só Windows/Linux x86 — **não roda em macOS/ARM**. Domínio + fake = ~90% testável no Mac.
- **Arquitetura porta/adaptador** (ADR-001): porta `FonteDeAquisicao`; `import nidaqmx` **só** em `aquisicao/daqmx.py` e **lazy** (teste-guarda de arquitetura via AST trava o resto).
- **Norte de design mudou (ADR-010):** o espelho de produto passou do **FlexLogger** para o **Lynx (AqDados + AqDAnalysis)** — o tio **domina o Lynx** e só está *aprendendo* o FlexLogger (trial pago). FlexLogger fica como referência **técnica** do driver. **Regra operacional:** dúvida de produto → pesquisar AqDados/AqDAnalysis (`docs/referencia-lynx.md`); dúvida técnica do driver → FlexLogger/NI-DAQmx (`docs/referencia-flexlogger.md`).
- **Estratégia de saída (ADR-011):** o software faz **aquisição + calibração**; a **análise continua no AqDAnalysis** do tio (não reescrevemos FFT/fadiga). Interop por **exportadores plugáveis**: CSV, **TXT** (que o AqDAnalysis importa; `.LDT` é proprietário, **não geramos**) e **Excel** (CSV-Excel-BR com `;`/vírgula, e/ou `.xlsx` via `openpyxl`). Extensão ≠ formato: converter conteúdo, nunca renomear.
- **Armadilha do strain:** defaults da API são full-bridge 350 Ω / 2,5 V; o 9235 é **quarter-bridge 120 Ω / 2,0 V**. Errado dá número plausível **sem erro**. Travado por teste-guarda e por `ConfigStrain`.
- **Privacidade:** prints do tio têm nomes de clientes/obras → **não versionados** (ficam em `docs/img/`, ignorada). Só a análise textual está no repo.

## 3. O que já foi feito (nesta sessão)

**Virada de norte (docs):** analisados 15 prints (AqDados/AqDAnalysis/FlexLogger). Criados `docs/referencia-lynx.md`, **ADR-010** (Lynx primário, revisa o 008), **ADR-011** (exportadores + não reescrever análise + Excel). `CONTEXT.md` ganhou vocabulário do Lynx (Aferição, Balanço, Repouso, Shunt Cal, Consulta, `.LDT`, Exportador) e unidades reais (µm/m, mm/s²). `respostas-tio.md` registra as mensagens. ADR-008 marcado **parcialmente substituído**; ADR-006 ganhou pendência (regressão linear + correlação, à la AqDados).

**Integração tensão+strain (código, TDD):** `executar_ensaio` particiona canais pelo campo `tipo` (`tensao`/`strain`) via `_ler_por_tipo`, lê cada grupo na sua task e grava junto, na ordem do config; tara vale para os dois. Domínio **valida o `tipo`**. Demo do Mac passou a mostrar microstrain (`canais.exemplo.toml` ativou `Mod3/ai0`).

**Aquisição contínua (código, TDD — ADR-007 → Aceito):**
- Porta ganhou `transmitir_tensao`/`transmitir_strain` (geradores de blocos).
- `fake` fatia listas sintéticas em blocos; `daqmx` usa `sample_mode=CONTINUOUS` + leitura por bloco, **encerrando a task limpo**.
- `GravadorEnsaioCsv` (context manager): grava CSV em **append** com `tempo_s` contínuo entre blocos. `gravar_ensaio` finito virou o caso de um bloco dele (sem duplicação).
- `executar_ensaio_continuo`: costura tensão+strain bloco a bloco (`zip`), com tara, parada por **`duracao_s`** e por **Ctrl-C** (callback `parar`, ligado ao SIGINT na CLI).
- CLI: `--continuo`, `--duracao-s`, `--bloco`.
- Refactor: extraída a montagem de canais no `daqmx` (reusada por finito+contínuo); validação de contagens unificada na persistência.

**Validação no Windows (Fase 2 fechada):** Win 11, Python 3.12.10, `pip install -e .[hardware]`, **70 passed**. Dispositivos simulados (cDAQ-9184 + 2× 9205 + 9235). As 4 validações do runbook `docs/validacao-windows.md` passaram: finita (CSV com tensão + µε), contínua por duração (10240 linhas, tempo 0→9.999 sem reinício), contínua por Ctrl-C (parada limpa, CSV íntegro), armadilha do strain (quarter-bridge/120 Ω/2,0 V). Registrado nos ADR-007/009 e CHANGELOG. **Número físico fica para a Fase 4.**

**Git:** 5 commits na `develop` (docs Lynx; feat tensão+strain; feat aquisição contínua; docs TXT temporário; docs validação Windows + remoção do TXT). **PR #4** develop→main aberta com descrição completa. O `VALIDAR-NO-WINDOWS.txt` (prompt usado no Windows) já foi **removido**.

## 4. Estado atual

- **70 testes verdes** no Mac (`uv run pytest`), sem `nidaqmx`. Teste-guarda de arquitetura e anti-armadilha do strain verdes.
- **Funciona:** porta multi-canal (finito + streaming), fake e daqmx, conversão pontos/linear, tara, CSV (batch e incremental), CLI finita e contínua. Validado no Windows simulado.
- **Fase 2 (backend) = FECHADA.** Working tree limpo.
- **PR #4** develop→main aberta: <https://github.com/Carti011/ensaios-ni/pull/4> — aguardando **merge manual do Weslley** (merge na main é só dele).

## 5. Bloqueios e dependências

- **Merge da PR #4**: o Weslley faz no GitHub. Depois, sincronizar a `develop` com a `main`.
- **Layout exato do TXT do AqDAnalysis** (incógnita do ADR-011): separador, cabeçalho, taxa, **decimal com vírgula** (padrão BR/Lynx). Fechar testando o "Importa Arquivo Texto" no Windows ou na doc da Lynx. **Não bloqueia** os exportadores CSV/Excel.
- **Número físico do strain**: só no hardware do tio (Fase 4).

## 6. Próximos passos (Fase 3 — em OUTRO chat)

1. **Exportadores plugáveis (ADR-011)** — começar pelos testáveis no Mac, via TDD:
   - **CSV-Excel-BR**: variante do CSV com separador `;` e **decimal vírgula** (abre certo no Excel em português).
   - **`.xlsx` nativo** via `openpyxl` (extra opcional no `pyproject`) — o "já vem no Excel" que o tio adora.
   - **TXT para o AqDAnalysis**: layout a descobrir (ver bloqueio acima); implementar quando o formato estiver fechado.
   - Exportação **seletiva** de sinais (nem todo canal vai pra todo arquivo).
2. **Dashboard (Fase 3)** — vira um **ADR de escolha de stack** (Plotly Dash p/ tempo real vs React+FastAPI). Referências de UX no `docs/referencia-lynx.md` (cursores ΔY/ΔT/1-ΔT=Hz; **XY graph** = carga×deformação).
3. **Refinamento da calibração (ADR-006)** — suportar **regressão linear** (com correlação) e "Ganho e Ponto de Referência", além da interpolação por segmento.
4. **Sincronização por start-trigger** das tasks tensão×strain (ADR-007/009) — só valida no Windows.
5. **Fase 4** — validar número físico no hardware do tio, com `docs/validacao-windows.md`.

## 7. Artefatos relevantes

- **Código:** `aplicacao/ensaio.py` (`executar_ensaio`, `executar_ensaio_continuo`, `_ler_por_tipo`, `_abrir_fluxos`), `aquisicao/{porta,fake,daqmx}.py`, `persistencia/csv_ensaio.py` (`GravadorEnsaioCsv`, `gravar_ensaio`), `__main__.py` (CLI), `aplicacao/demo.py`.
- **Decisões:** `docs/adr/006`–`011`; `docs/referencia-lynx.md`; `docs/referencia-flexlogger.md`; `docs/respostas-tio.md`; `docs/validacao-windows.md`.
- **Interface de streaming da porta:**
  ```python
  def transmitir_tensao(self, canais: list[str], taxa_hz: float, amostras_por_bloco: int) -> Iterator[dict[str, list[float]]]: ...
  def transmitir_strain(self, canais: list[str], taxa_hz: float, amostras_por_bloco: int) -> Iterator[dict[str, list[float]]]: ...
  ```
- **Caso de uso contínuo:**
  ```python
  executar_ensaio_continuo(fonte, canais, taxa_hz, caminho, amostras_por_bloco,
                           amostras_tara=0, duracao_s=None, parar=None)
  ```
- **Comandos:**
  - `uv run pytest` → **70 passed**.
  - Demo finita: `PYTHONPATH=src uv run python -m ensaios_ni --amostras 8 --taxa 16 --saida /tmp/ensaio.csv`
  - Demo contínua: `PYTHONPATH=src uv run python -m ensaios_ni --continuo --fonte fake --taxa 10 --bloco 4 --duracao-s 1 --saida /tmp/continuo.csv`
  - Windows real: `python -m ensaios_ni --continuo --fonte daqmx --config config/canais.toml --taxa 1024 --bloco 256 --duracao-s 10 --saida ensaio.csv`

## 8. Como iniciar a próxima sessão (no Mac, outro chat)

1. Ler este handoff, `CLAUDE.md`, `CONTEXT.md`, e os **ADR-010, ADR-011** (a virada de norte e a estratégia de exportação).
2. `uv run pytest` → **70 passed**. Se não, recriar venv (`uv venv --python 3.12`).
3. Confirmar com o Weslley se a **PR #4 foi mergeada** na `main`. Se sim, sincronizar a `develop`.
4. Atacar a **Fase 3 — exportadores** (passo 1 acima), via TDD, começando pelos testáveis no Mac: **CSV-Excel-BR** e **`.xlsx` (openpyxl)**. Desenhar a interface de exportador a partir da série temporal já em memória (mesma que `gravar_ensaio`/`GravadorEnsaioCsv` consomem). Deixar o **TXT-AqDAnalysis** para quando o layout estiver fechado.
5. Regras: import `nidaqmx` só no `daqmx.py` (lazy); teste-guarda verde; strain nunca usa defaults da API; commits separados por camada; nada de commit/push/merge autônomo; português em tudo.
