# Handoff: levantamento de requisitos do tio + 3 frentes implementadas (buffer -200279, filtro de ruído, formulário do canal)

**Data:** 2026-07-06
**Status:** em andamento — **PONTO DE ENTRADA da próxima sessão.** Código pronto e **289 testes verdes no Mac**, **não commitado** (5 commits preparados, aguardando o Weslley mandar). Duas frentes ficaram **aguardando decisão** dele.

> **Fonte única do status é o [roadmap.md](../roadmap.md); o backlog é o [tarefas-futuras.md](../tarefas-futuras.md).** Este é o handoff mais recente — leia-o primeiro. O anterior ([Parte A do ADR-023 + prep do levantamento](handoff-2026-07-04-a3-completa-e-prep-levantamento-requisitos.md)) preparou a sessão que este fecha.

## 1. Objetivo

Substituir o **FlexLogger** (única peça paga da pilha NI) por software próprio sobre o **NI-DAQmx** (gratuito), para o tio (OFM Engenharia: cDAQ-9184 + 2× 9205 + 1× 9235). **Critério de sucesso: o tio largar o FlexLogger.** Esta sessão (1) fez o **levantamento de requisitos** a partir de imagens + áudios que o tio enviou e (2) implementou **3 frentes** que saíram desse levantamento.

## 2. Contexto essencial

- **Stack:** Python 3.12, `pytest`, `uv` (Mac). Extras: `[hardware]` (`nidaqmx`, só Windows/Linux x86), `[gui]` (`PySide6`+`pyqtgraph`), `[excel]` (`openpyxl`), `[build]` (`pyinstaller`). Core: `tomlkit`. ~90% testável no Mac com o `fake`.
- **Arquitetura porta/adaptador ([ADR-001](../adr/001-arquitetura-porta-adaptador.md)):** `import nidaqmx` só em `aquisicao/daqmx.py` (lazy); `import PySide6` só em `apresentacao/qt/`. Guardas de AST travam o resto. Presenter puro (`apresentacao/*.py`) + Widget fino (`apresentacao/qt/*.py`) — [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md).
- **Armadilha do strain:** 9235 é quarter-bridge 120 Ω / 2,0 V; os defaults da API (full-bridge 350 Ω / 2,5 V) dão número plausível e errado sem erro. (Confirmado 1:1 com o FlexLogger do tio nesta sessão.)
- **Onde estamos:** Fases 0–4 ✅; Fase 5 🟡 (validação funcional 29/06 + teste de campo 03/07); Fase 6 🟡. Depois: Fase 7 (FFT ao vivo, [ADR-021](../adr/021-fft-ao-vivo-paridade-dinamica.md)).
- **Regra de mídia do tio:** imagens/áudios **nunca** vão pro repo; só a análise textual ([onde-pesquisar.md](../onde-pesquisar.md)). As mídias desta sessão foram **apagadas**.

## 3. O que já foi feito (nesta sessão)

**Levantamento de requisitos (imagens + 3 áudios do tio, transcritos com `mlx_whisper`, tudo já apagado):**
- **Erro ao gravar tem nome:** print do nosso software no Windows dele mostrou o **DAQmx `-200279`** (buffer overrun na aquisição contínua — não é chassi/rede).
- **Filtro de ruído:** pediu filtro para ver o "sinal verdadeiro" no gráfico ruidoso.
- **Exportação "coluna só":** o TXT abre no bloco de notas em uma coluna; quer colunas separadas com a **unidade embaixo do nome**.
- **Prefere ler em voltagem (mV/V) e correlacionar**, inclusive no strain ("pra fazer a curva e outras ligações").
- **FlexLogger dele** confirma os parâmetros do 9235 (gage factor 2,14, quarter/120/2V) e mostra **Live ε + Raw mV/V** — evidência do pedido de V/V. Registrado em [referencia-flexlogger.md §6](../referencia-flexlogger.md).
- Respostas às 3 perguntas: (1) "lê bonitinho, só dá erro depois de um tempinho" (não confirmou se o CSV sai completo); (2) afere strain pela leitura de tensão do canal, prefere voltagem; (3) NI-MAX mostra o 9235 em **µε**, não V/V.

**3 frentes implementadas por TDD (289 testes verdes):**
1. **fix `-200279` (buffer overrun)** — `_tamanho_buffer_continuo` no [daqmx.py](../../src/ensaios_ni/aquisicao/daqmx.py) dá **folga** ao buffer de entrada na aquisição contínua (o maior entre 10× o bloco e 5 s), mantendo o `read` por bloco fixo. Testado por mock; **validação real só no Windows** (não reproduz no Mac/simulado).
2. **Filtro de ruído ao vivo** — `dominio/filtro.py::media_movel` (média móvel centrada, pura) + `QuadroAoVivo.suavizar` + controle **"Suavizar ruído"** (janela em pts) no rodapé do dashboard. **Só visualização** — o CSV/laudo mantém o dado cru (rastreabilidade), como a seleção de canais.
3. **Formulário do canal** — exibe números em **decimal vírgula-BR** (`2,14`; o parse já aceitava os dois) e **validação inline** (Aplicar só habilita com endereço + unidade; fim do popup pós-clique). Fecha as pendências 7 e 8 do Panorama.

**Documentação atualizada:** CHANGELOG, [roadmap.md](../roadmap.md), [tarefas-futuras.md](../tarefas-futuras.md) (Panorama de 15, subseção do levantamento, itens 3/4/5/9/10), [referencia-flexlogger.md](../referencia-flexlogger.md) §6, [CONTEXT.md](../../CONTEXT.md) (termo **Razão de ponte / mV/V**).

**Descartado de propósito:** a tradução amigável do `-200279` em `erros.py` (o Weslley quis **resolver a causa, não maquiar a mensagem**).

## 4. Estado atual

- **289 testes verdes** no Mac (`uv run pytest`), sem `nidaqmx`. Guardas de AST verdes.
- **Working tree sujo, nada commitado.** 13 arquivos modificados + 2 novos (`dominio/filtro.py`, `tests/dominio/test_filtro.py`).
- **5 commits preparados** (ver §7) — backend/frontend separados, nenhum misturando camadas, sem `Co-authored-by`.
- **`.exe` do tio está desatualizado** (sem o fix do buffer, sem a config de canais na UI) — **rebuildar antes do próximo envio**.
- **Git:** `develop` (a PR para `main` segue pendente/opcional, decisão do Weslley).

## 5. Bloqueios e dependências

- **Commitar/pushar** — decisão do Weslley (nada autônomo). Os 5 commits estão prontos em §7.
- **Validar o fix do `-200279`** — só no Windows/hardware do tio (não reproduz no Mac).
- **TXT/Excel colunado (AGUARDA DECISÃO)** — o backlog manda "não especular antes de validar no AqDAnalysis". O "coluna só" do Excel é config regional dele (o `;` não separou); o **`.xlsx` nativo já resolveria** (não depende de separador). Precisa de ida ao Windows/AqDAnalysis, não de código às cegas.
- **V/V do strain (AGUARDA DECISÃO → vira ADR)** — muda a **porta** e o modelo de aferição. Rota a decidir: (a) capturar V/V no strain, (b) só exibir V/V ao lado do µε, (c) manter como está. Evidência forte no [referencia-flexlogger.md §6](../referencia-flexlogger.md).

## 6. Próximos passos (ordenados)

1. **Commitar** os 5 commits de §7 (quando o Weslley mandar).
2. **Abrir o ADR do V/V do strain** (ADR-024) decidindo a rota a/b/c — é o pedido mais estrutural do tio; confirmar a assinatura da leitura de bridge V/V (`BridgeUnits`) contra a doc do `nidaqmx` no Windows (não inventar).
3. **Rebuildar o `.exe`** (Windows) com o fix do buffer + config de canais na UI, e reenviar ao tio para validar o `-200279` e o Iniciar no hardware real.
4. **TXT/Excel** — resolver junto do tio no Windows/AqDAnalysis (via A: TXT legítimo dele; via B: testar a importação lá). Só então mexer no formato.
5. Backlog restante em [tarefas-futuras.md](../tarefas-futuras.md): sincronização tensão×strain, Parte B (discovery), FFT ao vivo (Fase 7), robustez de longa duração.

## 7. Artefatos relevantes

**Commits preparados (backend/frontend separados, PT, sem Co-authored-by):**

1. `fix(aquisicao): buffer com folga corrige overrun -200279 na aquisição contínua` — `src/ensaios_ni/aquisicao/daqmx.py`, `tests/aquisicao/test_daqmx.py`
2. `feat(dominio): filtro de ruído por média móvel para visualização` — `src/ensaios_ni/dominio/filtro.py`, `src/ensaios_ni/apresentacao/monitor.py`, `tests/dominio/test_filtro.py`, `tests/apresentacao/test_quadro.py`
3. `feat(apresentacao): controle de filtro de ruído no dashboard` — `src/ensaios_ni/apresentacao/qt/janela.py`, `tests/apresentacao/test_janela_qt.py`
4. `feat(apresentacao): decimal vírgula-BR e validação inline no formulário do canal` — `src/ensaios_ni/apresentacao/qt/editor_canais.py`, `tests/apresentacao/test_editor_canais_qt.py`
5. `docs: levantamento de requisitos do tio (04/07) e registro das entregas` — `CHANGELOG.md`, `CONTEXT.md`, `docs/referencia-flexlogger.md`, `docs/roadmap.md`, `docs/tarefas-futuras.md`

> O CHANGELOG vai inteiro no commit 5 (um só arquivo tocado por várias features; `git add -p` interativo não roda neste ambiente).

**Núcleo do fix `-200279`** (`daqmx.py`):

```python
_FATOR_BUFFER_CONTINUO = 10
_SEGUNDOS_BUFFER_MINIMO = 5.0

@staticmethod
def _tamanho_buffer_continuo(taxa_hz: float, amostras_por_bloco: int) -> int:
    return max(
        amostras_por_bloco * _FATOR_BUFFER_CONTINUO,
        int(taxa_hz * _SEGUNDOS_BUFFER_MINIMO),
    )
# nos transmitir_*: buffer = self._tamanho_buffer_continuo(...);
# _configurar_timing(task, CONTINUOUS, taxa, buffer); read segue por amostras_por_bloco
```

**Comandos:**
- Testes (Mac): `uv run pytest -q` → **289 passed**.
- Dashboard de hardware (Mac; Iniciar exige Windows): `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.hardware`
- Transcrever áudios do tio (se enviar mais): memória `transcrever-audios-mlx-whisper` (`mlx_whisper` large-v3-turbo offline, um por vez; `ffmpeg` `.ogg`→`.mp4` antes).

## 8. Como iniciar a próxima sessão

1. **Ler, nesta ordem:** este handoff → [roadmap.md](../roadmap.md) (status/fase) → [tarefas-futuras.md](../tarefas-futuras.md) (**Panorama de 15 pendências** no topo) → demais `.md` da raiz de `docs/` conforme necessidade. ADRs: só o índice [adr/README.md](../adr/README.md), abrir um específico só se um requisito colidir.
2. `uv run pytest -q` → **289 passed** (confirma a base).
3. **Confirmar com o Weslley:** se ele **commitou** os 5 commits de §7 (ou quer que eu commite agora) antes de assumir o estado do git.
4. **Decisões pendentes a puxar:** a **rota do V/V** (abrir ADR-024) e o **TXT/Excel** (depende do Windows/AqDAnalysis do tio).
5. Regras de sempre: `import nidaqmx` só em `daqmx.py` (lazy); `import PySide6` só em `apresentacao/qt/`; strain nunca usa os defaults da API; filtro/seleção de canais são **só visualização** (o CSV grava o cru); português em tudo; commits backend/frontend separados; **nunca commitar mídia do tio**; nada de commit/push/merge autônomo; ao mexer na contagem de testes, usar strings específicas, nunca `replace_all` de número cru.
