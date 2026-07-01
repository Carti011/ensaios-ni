# Handoff: gage factor por canal (ADR-020) + validação física funcional da Fase 5

**Data:** 2026-06-30  
**Status:** em andamento — Fase 5 (validação física) validada **funcionalmente**; ajustes finos e Fase 6 pela frente

## 1. Objetivo

Fazer o software de aquisição (substituto do FlexLogger) **funcionar no hardware real do tio** e
deixá-lo usável por ele. Esta sessão fechou duas coisas: registrar que a **primeira validação física
deu certo** (o software lê o sensor real e responde) e tirar o **gage factor do código** para a
config, por canal — destravando a calibração correta do strain sem editar código.

## 2. Contexto essencial

- **Stack:** Python 3.12, `pytest`, `nidaqmx` (extra `[hardware]`, só Windows), PySide6+pyqtgraph
  (extra `[gui]`), `tomlkit` (dep core). No Mac: `uv`.
- **Arquitetura porta/adaptador** ([ADR-001](../adr/001-arquitetura-porta-adaptador.md)): tudo
  depende da porta `FonteDeAquisicao`; só `aquisicao/daqmx.py` importa `nidaqmx` (lazy). ~90% testável
  no Mac com o adaptador `fake`. Teste-guarda de AST trava imports indevidos.
- **3 ambientes:** Mac (dev/testes), Windows do dev (simulado NI-MAX), Windows do tio (hardware real).
- **Armadilha do strain (maior risco):** os defaults da API NI são full-bridge 350 Ω / 2,5 V; o 9235
  é **quarter-bridge 120 Ω / 2,0 V**. Errar dá número **plausível e errado, sem lançar erro**. Travada
  por teste-guarda e pelos defaults seguros do `ParametrosStrain`.
- **Critério de sucesso do projeto:** o tio largar o FlexLogger. A validação numérica objetiva é
  **bater com o test panel do NI-MAX** no mesmo canal.

## 3. O que já foi feito (nesta sessão)

- **Validação física FUNCIONAL no hardware real do tio (29/06/2026).** O software leu o **NI 9235
  real** (`simulado=False`) e respondeu corretamente à deformação: o tio colou o gage numa chapa e
  aplicou força — o gráfico subiu/desceu coerente com a direção da força. Confirma que reconhece a
  DAQ, recebe o sinal do sensor real e reage. **Era o objetivo da ida — funciona.**
- **Gage factor (e parâmetros do extensômetro) por canal na config — [ADR-020](../adr/020-parametros-de-strain-por-canal.md), TDD, 185 testes verdes:**
  - Domínio (`dominio/canais.py`): novo value object `ParametrosStrain` + campo `Canal.strain`;
    `carregar_canais` lê `gage_factor`, `poisson`, `resistencia`, `resistencia_cabo` do `canais.toml`,
    por canal, com defaults seguros do 9235 e validação de número.
  - Adaptador (`aquisicao/daqmx.py`): usa os parâmetros **por canal**; `ConfigStrain` removido.
    Excitação (2,0 V) e ponte (quarter-bridge) ficam **fixas de propósito** (segurança).
  - CLI (`__main__.py`): injeta os canais no `AdaptadorDaqmx(canais=...)` — fim do gage factor fixo
    (2,15, errado) e do script manual.
  - Config (`config/canais.exemplo.toml`): campos documentados, exemplo com `gage_factor = 2.14`.
- **Documentação da sessão:** ADR-020 criado; ADR-009 (pendência "por-canal" marcada feita); índice
  de ADRs, CHANGELOG, roadmap, tarefas-futuras e o range no CLAUDE.md atualizados; brief no cofre
  atualizado.
- **Confirmado em campo pelo tio:** gage factor real = **2,14**; **só strain conectado** (não há
  sensor de tensão para testar o 9205); **cabo curto** (lead wire ≈ 0, default ok).

## 4. Estado atual

- **Funciona:** ciclo ler → calibrar → gravar → exportar (CLI + dashboard) no Mac com `fake`; e a
  leitura real do 9235 no hardware do tio responde à deformação.
- **185 testes verdes** no Mac (`uv run pytest`).
- **NÃO fechado (e não confundir com validação):** a comparação numérica NI-MAX × software. Na ida o
  NI-MAX estava em **V/V** e o software em **µε** (unidades diferentes) e só se mediu o repouso. O
  offset de repouso bruto foi alto/instável — esperado de ponte não-nulada; por isso a comparação
  certa é por **variação** (carregado − repouso), que cancela o offset.
- **Commits desta sessão (branch `develop`, sem push):** `feat` do backend (gage factor por canal) e
  `docs` (ADR-020 + atualizações). Backend e docs em commits separados (regra do projeto).

## 5. Bloqueios e dependências

- **Acesso ao hardware/Windows do tio** para: fechar a comparação numérica com o NI-MAX e validar o
  TXT no AqDAnalysis. Fora do Mac — depende de visita ou de arquivos do tio.
- O tio vai **documentando o que quer adicionar/remover/ajustar**; o Weslley traz e lapidamos.
- Nenhum bloqueio de código no Mac.

## 6. Próximos passos (o planejamento completo)

**Onde estamos no plano de fases:** Fases 0–4 ✅ (backend + dashboard). **Fase 5 🟡** (validação
física): funcional feita; faltam os ajustes finos. **Fase 6 ⬜** (empacotamento & adoção).

Ordem acordada com o Weslley, do mais concreto (no Mac) ao mais externo (no tio):

1. **[FEITO] Parametrizar o gage factor** — ADR-020, esta sessão.
2. **PRÓXIMO PASSO → Launcher do dashboard com hardware real.** Hoje `apresentacao/qt/janela.py`
   (`__main__`) chama `abrir()` → `_demonstracao()` → **demo fake**. Não existe forma oficial de abrir
   o dashboard completo (metadata/exportar/tara) ligado ao hardware. Criar um entrypoint (ex.:
   `python -m ensaios_ni.apresentacao.qt.hardware --config ... --taxa ... --bloco ...`) que monte
   `MonitorAoVivo(AdaptadorDaqmx(canais=canais), canais, ...)` e abra `JanelaMonitor`. Código no Mac
   (testável com `fake`/smoke headless), valida no Windows. É **frontend** → commit separado.
3. **Empacotar `.exe`** (Fase 6, PyInstaller) — o tio não roda `pip install`; sem isso, adoção = 0.
   Maior bloqueador de adoção. Preparar o build no Mac, gerar/testar no Windows.
4. **Fechar a validação numérica no hardware (próxima visita ao tio):** comparar a **variação**
   (carregado − repouso) NI-MAX × software no mesmo canal/unidade; e **importar o TXT no AqDAnalysis**
   dele (ajustar separador/decimal/cabeçalho se o wizard pedir). Roteiro:
   [guia-teste-hardware.md](../guia-teste-hardware.md).

**Backlog priorizado (pedido direto do tio, 30/06):** capturar a **leitura ao vivo na aferição** — o
tio: *"preciso poder dar a curva de validação quando eu quiser calibrar uma célula de carga ou um
acelerômetro; falar pra ele que o valor de tensão que está lendo é tal valor de engenharia;
correlacionar: esta tensão é tanto de carga"*. A aferição por regressão já existe na UI ([ADR-017](../adr/017-afericao-na-ui-e-escrita-de-config.md)),
mas a tensão é digitada à mão — falta o "Leitura do A/D" do AqDados (capturar a tensão atual ao
aplicar a carga). Ver [tarefas-futuras.md](../tarefas-futuras.md).

**Backlog (não bloqueia):** FFT/frequência ao vivo (paridade FlexLogger, decidir por ADR);
sincronização tensão×strain por start-trigger; robustez de longa duração (rotação de arquivo,
recuperação de rede). Tudo em [tarefas-futuras.md](../tarefas-futuras.md).

## 7. Artefatos relevantes

- **Código tocado:** `src/ensaios_ni/dominio/canais.py` (`ParametrosStrain`, `Canal.strain`,
  carregamento), `src/ensaios_ni/aquisicao/daqmx.py` (params por canal), `src/ensaios_ni/__main__.py`
  (CLI injeta canais), `config/canais.exemplo.toml`.
- **Testes:** `tests/dominio/test_canais.py`, `tests/aquisicao/test_daqmx.py`.
- **Config de strain por canal (formato novo no `canais.toml`):**
  ```toml
  [canais."cDAQ9184-1820306Mod3/ai0"]
  tipo = "strain"
  unidade = "µε"
  rotulo = "Sg1 bico"
  gage_factor = 2.14          # por canal; omitido = default seguro do 9235
  ganho = 1000000.0           # strain → microstrain
  offset = 0.0
  ```
- **Comandos:**
  - Testes (Mac): `uv run pytest -q` → 185 passed.
  - Dashboard demo (Mac): `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.janela`.
  - Ensaio real (Windows do tio): `python -m ensaios_ni --fonte daqmx --config config/canais.toml --taxa 1024 --amostras 1024 --saida ensaio.csv`.
- **Handoff da sessão de campo (no PC do tio, pode não estar no repo):**
  `handoff-2026-06-29-validacao-fisica-strain-e-fft.md`; protótipo de FFT em `scripts/monitor_strain_fft.py`.

## 8. Como iniciar a próxima sessão

1. Ler **este handoff** + [roadmap.md](../roadmap.md) (status) — não precisa reler todos os ADRs.
2. Rodar `uv run pytest -q` (esperar 185 verdes) para confirmar o ponto de partida.
3. Começar pelo **item 2 — launcher do dashboard com hardware real** (seção 6). Abrir
   `src/ensaios_ni/apresentacao/qt/janela.py` (ver `abrir()`/`_demonstracao()`) e
   `src/ensaios_ni/apresentacao/monitor.py` (`MonitorAoVivo`). É feature nova → seguir TDD; é
   **frontend** → commit separado do backend desta sessão.
4. Confirmar com o Weslley se quer o launcher como módulo novo (`qt/hardware.py`) ou argumentos no
   entrypoint atual.
