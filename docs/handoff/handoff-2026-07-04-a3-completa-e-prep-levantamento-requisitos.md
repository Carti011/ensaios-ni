# Handoff: Parte A do ADR-023 concluída (config de canais na UI) + preparação para o levantamento de requisitos do tio

**Data:** 2026-07-04
**Status:** em andamento — **PONTO DE ENTRADA da próxima sessão.** A `develop` está pushada e **sem PR** para a `main` (decisão do Weslley: deixar a PR **pendente/opcional**, ele abre se quiser). A próxima sessão é um **levantamento de requisitos** a partir de **imagens + áudios que o tio enviou**.

> **Fonte única do status é o [roadmap.md](../roadmap.md); o backlog é o [tarefas-futuras.md](../tarefas-futuras.md).** Este handoff é o mais recente — leia-o primeiro. O anterior ([feedback do tio + achados do Windows + correção do NI-MAX](handoff-2026-07-04-feedback-do-tio-e-achados-do-windows.md)) cobre a base que esta sessão estendeu.

## 1. Objetivo

Substituir o **FlexLogger** (única peça paga da pilha NI) por software próprio sobre o **NI-DAQmx** (gratuito), para o tio (OFM Engenharia: cDAQ-9184 + 2× 9205 + 1× 9235). **Critério de sucesso: o tio largar o FlexLogger.** Esta sessão (1) documentou o feedback de campo do tio (áudios de 03/07) e corrigiu uma nota errada sobre o NI-MAX, e (2) **fechou a Parte A do [ADR-023](../adr/023-configuracao-de-canais-na-ui.md)** (configuração de canais na UI), tirando do tio a edição manual do `canais.toml`.

## 2. Contexto essencial

- **Stack:** Python 3.12, `pytest`, `uv` (Mac). Extras: `[hardware]` (`nidaqmx`, só Windows/Linux x86), `[gui]` (`PySide6`+`pyqtgraph`, ARM ok), `[excel]` (`openpyxl`), `[build]` (`pyinstaller`). Core: `tomlkit`. ~90% testável no Mac com o `fake`.
- **Arquitetura porta/adaptador ([ADR-001](../adr/001-arquitetura-porta-adaptador.md)):** `import nidaqmx` só em `aquisicao/daqmx.py` (lazy); `import PySide6` só em `apresentacao/qt/`. Guardas de AST travam o resto. **Presenter puro (`apresentacao/*.py`) + Widget fino (`apresentacao/qt/*.py`)** ([ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md)).
- **Armadilha do strain (inalterada):** 9235 é quarter-bridge 120 Ω / 2,0 V; os defaults da API (full-bridge 350 Ω / 2,5 V) dão número plausível e errado sem erro.
- **Filosofia de produto:** núcleo técnico segue o padrão NI; fluxo/vocabulário espelham o AqDados (Lynx); a entrega (UX) a gente melhora. Usuário é o **tio**. Ver [onde-pesquisar.md](../onde-pesquisar.md).
- **Onde estamos:** Fases 0–4 ✅; Fase 5 🟡 (validação funcional 29/06 + teste de campo 03/07); Fase 6 🟡 (`.exe` builda e adquire no simulado; **Parte A do ADR-023 concluída em 04/07**). Depois: Fase 7 (FFT ao vivo, [ADR-021](../adr/021-fft-ao-vivo-paridade-dinamica.md)).

## 3. O que já foi feito (nesta sessão)

**Documentação (feedback do tio + correção):**
1. **Transcrição de 3 áudios do tio** (teste de campo 03/07) com `mlx_whisper` → registrado em [tarefas-futuras.md](../tarefas-futuras.md): funciona/lê a deformação; **erro recorrente ao gravar** (a arrumar); pedido de **ver a tensão V/V do strain**. (Receita de transcrição na memória `transcrever-audios-mlx-whisper`.)
2. **Correção da nota errada do NI-MAX** ([ADR-022](../adr/022-empacotamento-exe-pyinstaller.md) + CHANGELOG + roadmap): "fechar o NI-MAX derruba a leitura" era **enganoso** — o dispositivo simulado vive no **driver** e roda com o NI-MAX fechado; a aquisição é real **pela arquitetura**.

**Feature — Parte A do ADR-023 (config de canais na UI), toda por TDD:**
3. **A3 — gerência de perfis completa** (`apresentacao/perfis.py` + `qt/hardware.py`): `criar`, `importar`, `renomear`, `remover`, `duplicar`, `exportar` — todos com validação de nome e erros de domínio (`PerfilJaExiste`/`PerfilNaoExiste`/`NomeDePerfilInvalido`/`ImportacaoInvalida`). Importar reusa `carregar_canais` como rede de segurança (ADR-023 decisão 4); helpers `_destino_novo`/`_origem_existente` compartilhados.
4. **Fix do botão "Editar canais…" inerte** (descoberto no Windows 03/07): nasce desabilitado, habilita ao selecionar.
5. **Tela inicial reorganizada em dois grupos** (ações do ensaio selecionado × biblioteca/avulso), resolvendo o acúmulo de botões. Botões: `[Editar canais…] [Renomear…] [Duplicar] [Exportar…] [Remover]` (habilitados só com seleção) e `[Novo ensaio…] [Importar…] [Abrir configuração…]`.

**Commits na `develop` (cronológico):** correção do NI-MAX (`331b604`); handoff anterior (`a1baa63`); A3-criar (`35be127`/`d76f2bb`/`2817677`); A3-importar (`73d0dd5`/`47130e0`/`4b9f7eb`); tarefas do README+UX (`f444e17`); A3-renomear/remover (`ddb2bc6`/`de84e54`/`4457d31`); A3-duplicar/exportar (`a019a7f`/`d7c59ca`/`aa1328e`); docs de status + este handoff (a commitar).

## 4. Estado atual

- **281 testes verdes** no Mac (`uv run pytest`), sem `nidaqmx`. Guardas de AST verdes.
- **Parte A do ADR-023 = 100%** (A1 lista/abre · A2 editor de canais · A3 gerência). **Falta a Parte B** (discovery de dispositivos — só valida no Windows).
- **`.exe`:** builda e **adquire no simulado**; falta o **Iniciar no hardware real do tio**. **Atenção:** o `.exe` que o tio tem é antigo (sem o fix do `nitypes` nem a config de canais na UI) — **rebuildar** antes do próximo envio.
- **Git:** `develop` **pushada** e **sem PR** para `main` (a PR #11 anterior já foi mergeada num ponto antigo; tudo desde então está só na `develop`). O Weslley **não quer abrir a PR agora** — fica pendente/opcional para ele testar no Windows via pull.
- **Working tree:** limpo após o commit final desta sessão.

## 5. Bloqueios e dependências

- **Abrir a PR `main ← develop`** é decisão do Weslley (ele deixou pendente de propósito).
- **Erro ao gravar (pendência 🔴):** travado esperando o **texto/print do erro** (perguntar ao tio).
- **Ver/capturar V/V do strain (🟠):** decisão de produto do Weslley + confirmar a API no Windows.
- **Parte B (discovery), validação numérica, TXT no AqAnalysis, `.exe` no hardware:** dependem do Windows/hardware do tio.

## 6. Próximos passos (ordenados)

1. **A PRÓXIMA SESSÃO É LEVANTAMENTO DE REQUISITOS.** O Weslley vai anexar **imagens** (várias) e **áudios** que o tio enviou (ele pediu ao tio um levantamento de requisitos). Fazer:
   - **Áudios → texto** com **`mlx_whisper`** (large-v3-turbo, offline, um arquivo por vez — receita completa na memória `transcrever-audios-mlx-whisper`; converter `.ogg`→`.mp4` com ffmpeg antes).
   - **Ler as imagens** com a ferramenta Read (suporta imagem). São prints do tio → **não versionar** (material do tio, [onde-pesquisar.md](../onde-pesquisar.md)); só a análise textual entra no repo.
   - **Sintetizar os requisitos:** o que o tio gostou, o que não gostou, o que falta. Cruzar com o [Panorama de 14 pendências](../tarefas-futuras.md) e com o feedback já registrado (erro ao gravar, V/V do strain). Atualizar `tarefas-futuras.md`/`referencia-lynx.md`/`CONTEXT.md` conforme surgir vocabulário ou requisito novo; abrir ADR se virar decisão.
2. **Perguntas ainda abertas ao tio** (levar quando possível): (a) **texto/print do erro** ao gravar; (b) como ele **afere strain** hoje (por V/V ou por gage factor); (c) unidade que o **NI-MAX** mostra no 9235 (V/V ou µε); (d) o teste de 03/07 foi via `.exe` ou `python -m`.
3. **Refinamentos rápidos no Mac** (se sobrar fôlego): decimal vírgula-BR no formulário do canal; validação inline no diálogo (pendências #7 e #8 do Panorama).
4. **Rebuild do `.exe`** (Windows) com tudo novo, e reenviar ao tio.

## 7. Artefatos relevantes

- **Código da Parte A (config de canais na UI):**
  - `src/ensaios_ni/apresentacao/perfis.py` — `BibliotecaDePerfis`: `listar`, `criar`, `importar`, `renomear`, `remover`, `duplicar`, `exportar`; erros `PerfilJaExiste`/`PerfilNaoExiste`/`NomeDePerfilInvalido`/`ImportacaoInvalida`; `pasta_padrao() = ~/ensaios-ni`.
  - `src/ensaios_ni/apresentacao/qt/hardware.py` — `TelaInicial` (dois grupos de botões, métodos `_criar_perfil`/`_importar_perfil`/`_renomear_perfil`/`_remover_perfil`/`_duplicar_perfil`/`_exportar_perfil`, todos testáveis; handlers modais com `# pragma: no cover`).
  - `src/ensaios_ni/apresentacao/{editor_canais.py, qt/editor_canais.py}` — editor de canais (A2, já existente).
  - Testes: `tests/apresentacao/test_perfis.py` (33) e `test_hardware.py`.
- **Interface nova (Presenter, testável no Mac):**
  ```python
  BibliotecaDePerfis(pasta).criar(nome) -> Perfil
  BibliotecaDePerfis(pasta).importar(origem, nome=None) -> Perfil   # valida via carregar_canais
  BibliotecaDePerfis(pasta).renomear(atual, novo) -> Perfil
  BibliotecaDePerfis(pasta).duplicar(nome, novo) -> Perfil
  BibliotecaDePerfis(pasta).remover(nome) -> None
  BibliotecaDePerfis(pasta).exportar(nome, destino) -> Path         # copia para fora da biblioteca
  ```
- **Transcrever áudios do tio (próxima sessão):** memória `transcrever-audios-mlx-whisper` — `mlx_whisper --model <snapshot large-v3-turbo> --language pt --output-format all` com `HF_HUB_OFFLINE=1`, **um arquivo por vez**; `ffmpeg -i x.ogg -c:a aac x.mp4` antes.
- **Comandos:**
  - Testes (Mac): `uv run pytest -q` → **281 passed**.
  - Tela inicial / dashboard de hardware (Mac; o Iniciar exige Windows): `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.hardware`
  - Demo `fake` (Mac): `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.janela`
  - Build (Windows): `pip install -e .[hardware,gui,excel,build]` && `pyinstaller packaging/ensaios-ni.spec`

## 8. Como iniciar a próxima sessão

1. **Ler, nesta ordem:** este handoff → [roadmap.md](../roadmap.md) (status) → [tarefas-futuras.md](../tarefas-futuras.md) (o **Panorama de 14 pendências** no topo) → os demais `.md` da raiz de `docs/` (contexto-hardware, onde-pesquisar, referencia-lynx, referencia-flexlogger, guia-teste-hardware, uso).
2. **ADRs — recomendação:** **não** precisa ler todos. Ler o **índice** [docs/adr/README.md](../adr/README.md) (uma linha por ADR) e abrir um ADR específico **só** se um requisito novo colidir com uma decisão. Os mais relevantes para requisitos: [023](../adr/023-configuracao-de-canais-na-ui.md) (config de canais), [021](../adr/021-fft-ao-vivo-paridade-dinamica.md) (FFT), [019](../adr/019-foco-em-validacao-fisica-e-adocao.md) (adoção acima de features), [011](../adr/011-estrategia-de-exportacao.md) (exportar/TXT), [001](../adr/001-arquitetura-porta-adaptador.md) (espinha dorsal).
3. `uv run pytest -q` → **281 passed** (confirma a base). Se faltar PySide, `uv sync` instala o `[gui]`.
4. **Processar os anexos do tio** (imagens + áudios) conforme §6.1 — é o foco da sessão: extrair o levantamento de requisitos e cruzar com o Panorama.
5. **Git:** a `develop` está pushada; confirmar com o Weslley se ele **abriu a PR** (ele a deixou pendente de propósito) antes de assumir que algo está na `main`.
6. Regras de sempre: `import nidaqmx` só em `daqmx.py` (lazy); `import PySide6` só em `apresentacao/qt/`; Presenter puro + widget fino; strain nunca usa os defaults da API; português em tudo (UI também); commits separados por camada; **nunca commitar dados/mídia do tio** (áudios/imagens ficam fora do repo); nada de commit/push/merge autônomo sem o Weslley pedir; ao mexer na **contagem de testes**, usar strings específicas, nunca `replace_all` de número cru.
