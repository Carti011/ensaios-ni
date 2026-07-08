# Handoff: feedback de campo do tio (áudios) + achados do teste no Windows + correção da nota do NI-MAX

**Data:** 2026-07-04
**Status:** aguardando decisão/informação — nada de código nesta sessão; **4 docs alterados e não commitados**. Frentes abertas: (1) abrir a PR dos 7 commits A1/A2 órfãos; (2) perguntas pendentes ao tio; (3) A3 (gerência de perfis) com prioridade elevada.

> **Fonte única do status é o [roadmap.md](../roadmap.md).** Este é o ponto de entrada da próxima sessão. O anterior ([config de canais na UI A1+A2 + fix do `.exe`](handoff-2026-07-03-config-canais-na-ui-a1-a2.md)) cobre a base que esta sessão estendeu. Sessão de **documentação e análise** — sem mudança em `src/`.

## 1. Objetivo

Substituir o **FlexLogger** (única peça paga da pilha NI) por software próprio sobre o **NI-DAQmx** (gratuito), para o tio (OFM Engenharia: cDAQ-9184 + 2× 9205 + 1× 9235). **Critério de sucesso: o tio largar o FlexLogger.** Esta sessão (1) absorveu o contexto do projeto, (2) **transcreveu 3 áudios de WhatsApp do tio** com o retorno do teste no hardware real e documentou o feedback, e (3) **corrigiu uma afirmação equivocada sobre o NI-MAX** descoberta ao analisar o teste do Weslley no Windows do dev.

## 2. Contexto essencial

- **Stack:** Python 3.12, `pytest`, `uv` (Mac). Extras: `[hardware]` (`nidaqmx`, só Windows/Linux x86), `[gui]` (`PySide6`+`pyqtgraph`, roda em ARM), `[excel]` (`openpyxl`), `[build]` (`pyinstaller`). Core: `tomlkit`. ~90% testável no Mac com o `fake`.
- **Arquitetura porta/adaptador ([ADR-001](../adr/001-arquitetura-porta-adaptador.md)):** `import nidaqmx` só em `aquisicao/daqmx.py` (lazy); `import PySide6` só em `apresentacao/qt/`. Guardas de AST travam o resto. Presenter puro + Widget fino ([ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md)).
- **Armadilha do strain (inalterada):** 9235 é quarter-bridge 120 Ω / 2,0 V; os defaults da API (full-bridge 350 Ω / 2,5 V) dão número plausível e errado sem erro.
- **Filosofia de produto:** núcleo técnico segue o padrão NI; fluxo/vocabulário espelham o AqDados (Lynx); a entrega (UX) a gente melhora. Usuário é o **tio**.
- **Onde estamos:** Fases 0–4 ✅; Fase 5 🟡 (validação física funcional 29/06 + novo teste de campo 03/07); Fase 6 🟡 (`.exe` builda e adquire no simulado; config de canais na UI = frente de dev, A1/A2 feitas). Depois, Fase 7 (FFT ao vivo, [ADR-021](../adr/021-fft-ao-vivo-paridade-dinamica.md)).
- **Git (importante):** a **PR #11 foi mergeada** em 03/07 num ponto **anterior** ao trabalho A1/A2. Hoje há **7 commits na `develop`** (A1/A2 + limpeza + handoff de 03/07) **pushados** mas **sem PR aberta** para a `main`. O Weslley confirmou: "a PR está lá mas não foi aberta de verdade".

## 3. O que já foi feito (nesta sessão)

1. **Retomada de contexto** — li todos os `.md` da raiz (README, CONTEXT, CHANGELOG), os 8 `.md` da raiz de `docs/`, os 3 handoffs mais recentes, o índice de ADRs, e os ADR-001/022/023.
2. **Transcrição dos 3 áudios do tio** (`~/Downloads/WhatsApp Ptt 2026-07-03 at 14.46.03/14.46.55/14.47.50.ogg`):
   - Convertidos `.ogg` → `.mp4` (AAC) com **ffmpeg**; durações 1min42s / 8s / 23s.
   - Transcritos com **`mlx_whisper`** (0.4.3, Apple Silicon), modelo `mlx-community/whisper-large-v3-turbo` (o `large-v3` está com download **incompleto** no cache; o turbo está completo). Rodar **offline** (`HF_HUB_OFFLINE=1` + `--model <caminho do snapshot>`) porque a validação online do HF dá 401.
   - **Cuidado descoberto:** rodar os 3 num único comando batch **só salvou o áudio 1** (e com conteúdo trocado); e o Whisper **alucinou** no fim do áudio 1 (loop de "eu preciso..." além da duração real). Solução: transcrever **um por vez**. O Weslley confirmou que o fim do áudio 1 é só o corte do áudio (sem conteúdo novo).
3. **Análise do feedback + esclarecimentos do Weslley** (ver §7).
4. **Documentação em [tarefas-futuras.md](../tarefas-futuras.md):** seção "Feedback de campo — teste remoto do tio (03/07/2026)" + item 🔴 (erro ao gravar) + item 🟠 (ver/capturar V/V no strain).
5. **Achados do teste do Weslley no Windows** (ele conversou com o "Claude do Windows"), confirmados por mim no código:
   - "Editar canais…" não faz nada → **não é a A3 faltando só**; é **defeito de UX** (botão inerte) + a biblioteca de perfis **nasce vazia**. Documentado em tarefas-futuras.
   - "Iniciar" com o NI-MAX fechado → **esperado** (simulado vive no driver). Isso **contradiz** a nota de 02/07.
6. **Correção da nota equivocada do NI-MAX** em 3 lugares (ADR-022 como dono + CHANGELOG + roadmap apontando).
7. **Pesquisa técnica (web):** confirmado que o **9235 é ratiométrico** — mede **razão de ponte V/V** (`Vr = (Vch/Vex)carregado − (Vch/Vex)repouso`, ±29,4 mV/V), do qual o strain deriva pelo gage factor; o `nidaqmx` expõe `ai_bridge_units`/`BridgeUnits` (V/V). **Assinatura exata do método de bridge a confirmar no Windows** (regra: não inventar).

## 4. Estado atual

- **4 arquivos alterados e NÃO commitados** (working tree): `CHANGELOG.md`, `docs/adr/022-empacotamento-exe-pyinstaller.md`, `docs/roadmap.md`, `docs/tarefas-futuras.md`. Só documentação — `src/` intacto.
- **Testes não rodados nesta sessão** (não houve mudança em `src/`); a base era **242 testes verdes** no fim da sessão anterior.
- **Feedback do tio (teste no hardware real, 03/07):** o software **lê, identifica a DAQ e leu a deformação** aplicada na peça (9235). ✅ Funciona. Reportou um **erro recorrente ao gravar** (texto ainda desconhecido) e pediu para **ver/capturar a tensão do canal de strain**. Identificar "só um módulo" era **esperado** (teste com um módulo só — esclarecido pelo Weslley).
- **Windows do dev:** o Weslley testou o `.exe` (abrir `canais-simulado.toml` funciona; "Editar canais…" inerte; Iniciar com NI-MAX fechado funciona). Ele **desligou o Windows**; volta a ligar depois.
- **Transcrições** (`.srt`/`.txt`) estão só no **scratchpad** (efêmero) — ainda não movidas para lugar persistente. Os áudios **não** vão para o repo (política de material do tio, [onde-pesquisar.md](../onde-pesquisar.md)).

## 5. Bloqueios e dependências

- **Erro ao gravar (item 🔴):** bloqueado por **informação** — precisa do **texto/print exato do erro** (perguntar ao tio) para diagnosticar.
- **V/V no strain (item 🟠):** **decisão de produto** do Weslley — habilitar captura de V/V no strain, só exibir, ou manter cinza e explicar. Depende também de saber **como o tio afere strain hoje** (pergunta ao tio).
- **PR dos 7 commits A1/A2:** abrir é decisão do Weslley (`main` é produção; merge é dele).
- **Parte B (discovery) e validação numérica:** dependem do Windows/hardware do tio.
- **Confirmar:** se o teste de 03/07 rodou o **`.exe`** ou o `python -m` (define se avança o status da Fase 6).

## 6. Próximos passos (ordenados)

1. **Commitar os 4 docs desta sessão** (quando o Weslley pedir) — mensagem sugerida: `docs: registra feedback de campo do tio (03/07) e corrige a nota do NI-MAX`. Depois **abrir a PR** dos commits A1/A2 (`main ← develop`).
2. **Levar as perguntas ao tio** (§7) — o texto do erro é o que destrava o item 🔴.
3. **Frente Mac — A3 (gerência de perfis), TDD**, com **prioridade elevada**: sem ela a biblioteca de perfis nasce vazia e o editor (A2) fica inalcançável. Estende `apresentacao/perfis.py` (`criar`/`duplicar`/`renomear`/`remover`/importar) e a `TelaInicial`. **Junto:** corrigir o **botão "Editar canais…" inerte** (desabilitar sem seleção ou avisar).
4. **Diagnosticar o erro ao gravar** com `/diagnose` assim que houver o texto — hipóteses em [tarefas-futuras.md](../tarefas-futuras.md) (timeout/buffer da task contínua do 9235 no chassi Ethernet; erro no encerramento da gravação; `DaqError` não coberto por `apresentacao/erros.py`).
5. **Decidir e (se sim) implementar** a leitura de V/V do strain (refina ADR-017/020; pode virar ADR se entrar na porta).
6. **Rebuild do `.exe`** no Windows com o fix do `nitypes` + A1/A2 (o que o tio tem é antigo) e reenviar.
7. **Depois:** Fase 7 — FFT ao vivo ([ADR-021](../adr/021-fft-ao-vivo-paridade-dinamica.md)).

## 7. Artefatos relevantes

- **Transcrições limpas dos áudios (o retorno do tio):**
  - **Áudio 1 (1min42s):** "Funcionou! Ele dá umas travadinhas, mas funcionou. E tem esse erro — **começa a gravar e depois dá esse erro**, acontecendo direto. Mas ele lê bonitinho e **identifica a DAQ**. Tá identificando **só esse módulo** [esperado]. **Tá em cinza o 'capturar tensão'** — queria saber como capturar a tensão pra inserir o ponto. Essa é a placa do **strain gage** (9235, quarto de ponte 120 Ω); as outras (9205) só leem tensão. **Preciso capturar a tensão pra correlacionar e saber por que dá esse erro.** Ele **leu a deformação que apliquei na peça**." [fim = corte]
  - **Áudio 2 (8s):** "...mesmo rodando normal, ele fica **cinza o 'capturar tensão'**."
  - **Áudio 3 (23s):** "Tá tudo montadinho, ligado, tô com o **[NI-]MAX aberto**. Tá lendo, fazendo tudo perfeito. Só precisa refinar, mas tá ficando da hora."
- **Perguntas pendentes ao tio (o Weslley leva):**
  1. **Do erro:** print/texto exato do erro que aparece depois de começar a gravar; e o CSV sai completo ou o erro atrapalha a gravação?
  2. **Da calibração do strain:** no AqDados, ele afere o strain pela leitura de **tensão (V/V)** ou direto pelo **gage factor**? Qual o passo a passo?
  3. **Do NI-MAX:** o test panel do 9235 mostra o número em **V/V** ou em **microstrain (µm/m)**?
- **Comandos de transcrição (reproduzível no Mac):**
  ```bash
  # 1) converter (ffmpeg instalado via homebrew)
  ffmpeg -y -i "entrada.ogg" -c:a aac -b:a 128k "saida.mp4"
  # 2) transcrever OFFLINE com o modelo em cache (o large-v3 está incompleto; usar o turbo)
  MODEL=$(ls -d ~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/*/ | head -1)
  HF_HUB_OFFLINE=1 mlx_whisper --model "$MODEL" --language pt --output-format all --verbose False "saida.mp4"
  # OBS: transcrever UM ARQUIVO POR VEZ (batch de vários salvou só o 1º e trocou conteúdo)
  ```
  Transcrições geradas em: `/private/tmp/claude-501/-Users-carti011-cofre-codigo-ensaios-ni/125eef6d-445d-4764-911a-27060ef18887/scratchpad/audios/` (scratchpad, efêmero).
- **Docs alterados nesta sessão:** `docs/tarefas-futuras.md` (feedback + itens 🔴/🟠 + A3 elevada + fix do botão), `docs/adr/022-empacotamento-exe-pyinstaller.md` (correção da nota do NI-MAX — dono), `CHANGELOG.md` e `docs/roadmap.md` (mesma correção, apontando pro ADR-022).
- **Achado de código confirmado ([hardware.py](../../src/ensaios_ni/apresentacao/qt/hardware.py)):** `_editar_canais_do_selecionado()` (l.130) faz `currentItem()`; `if item is None: return None` → clique morre em silêncio. `BibliotecaDePerfis.listar()` faz `glob("*.toml")` em `~/ensaios-ni` (l.35 de `perfis.py`); pasta inexistente → lista vazia → botão inerte.

## 8. Como iniciar a próxima sessão

1. Ler **este handoff** + [roadmap.md](../roadmap.md) (status) + a seção "Feedback de campo (03/07)" em [tarefas-futuras.md](../tarefas-futuras.md). Não precisa reler todos os ADRs.
2. `uv run pytest -q` → confirmar **242 passed** (a base; nada em `src/` mudou nesta sessão).
3. **Perguntar ao Weslley:** (a) o tio já respondeu as 3 perguntas (§7)? (b) commitar/abrir a PR dos docs + A1/A2 agora? (c) confirmou se o teste de 03/07 foi `.exe` ou `python -m`?
4. **Decidir a frente:** no **Mac**, começar a **A3 (gerência de perfis)** com TDD + corrigir o botão "Editar canais…" inerte; se houver o texto do erro, abrir o `/diagnose` do "erro ao gravar"; no **Windows** (quando religado), rebuildar o `.exe` e testar.
5. Regras de sempre: `import nidaqmx` só em `daqmx.py` (lazy); `import PySide6` só em `apresentacao/qt/`; Presenter puro + widget fino; strain nunca usa os defaults da API; português em tudo (UI também); commits separados por camada; **nunca commitar dados reais do tio** (`config/canais.toml` é gitignored); nada de commit/push/merge autônomo sem o Weslley pedir; ao mexer na **contagem de testes**, usar strings específicas, nunca `replace_all` de número cru.
