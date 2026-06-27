# Handoff: Fase 4 fatia 3 — Aferição na UI (calibração por regressão + nome do sinal)

**Data:** 2026-06-27
**Status:** fatia 3 fechada e **commitada na `develop`** (3 commits, **sem push/merge**). 156 testes verdes.
Validada na tela pelo Weslley (5 screenshots). Próximo é a **fatia 4** (metadata + exportar pela UI +
**tara ao vivo**), idealmente em outro chat.

> **Fonte única do status é o [roadmap.md](../roadmap.md).** Este handoff é o ponto de entrada da
> próxima sessão; o anterior ([fatia 2 — XY e multicanal](handoff-2026-06-27-fase-4-fatia-2-xy-multicanal.md))
> cobre a base que esta fatia estendeu.

## 1. Objetivo

Construir a **fatia 3** do dashboard ([ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md) §plano de
fatias): deixar o tio **aferir um canal pela tela** (à la "Aferição por Regressão Linear" do
AqDados — [referencia-lynx.md §1.2–1.3](../referencia-lynx.md)) — tabela de pontos `(V, valor eng.)`
→ regressão → correlação % → **persistir no `canais.toml`** — e dar **nome humano** aos canais
(o "Nome do Sinal" do AqDados). É a **primeira vez que a UI escreve config**.

## 2. Contexto essencial

- **O backend de cálculo já existia** (regressão + correlação + tara no domínio, ADR-006). A fatia 3
  é **UI + escrever o TOML**, não lógica de cálculo nova.
- **Arquitetura mantida (ADR-015):** Presenter Python puro (testável no Mac sem display) + Widget
  PySide6 fino. `import PySide6` só em `apresentacao/qt/` (guarda de AST). `import nidaqmx` só em
  `daqmx.py`.
- **Decisões desta fatia ([ADR-017](../adr/017-afericao-na-ui-e-escrita-de-config.md)):**
  1. A UI escreve o TOML com **`tomlkit`** (preserva comentários; o `tomllib` é só leitura).
     `tomlkit` virou a **primeira dependência core** do projeto.
  2. **Só regressão + correlação** na UI (segmento e "Ganho e Ponto de Referência" ficam de fora).
  3. **Os pontos vivem no TOML** (fonte da verdade); o `Canal` calibrado por regressão guarda **só a
     `reta`** — o painel relê os pontos via `ler_pontos` ao abrir.
  4. **Nome do sinal:** campo `rotulo` no `Canal` + property `etiqueta` (= `rotulo or nome`); a UI
     exibe a etiqueta e guarda o endereço como identidade interna (`UserRole`/`itemData`).
  5. **A tara saiu do painel de aferição e foi para a fatia 4** (é por-ensaio, não persiste no TOML,
     exige estender o `MonitorAoVivo`).
- **Filosofia de produto (inalterada):** usuário é o **tio** (OFM); fluxo/vocabulário espelham o
  AqDados (Lynx); a entrega (UX) a gente melhora.

## 3. O que já foi feito (nesta sessão, TDD red-green-refactor)

**Backend — `feat(dominio)` (commit `999f7be`):**
- `dominio/canais.py`: campo opcional `rotulo` no `Canal` + property `etiqueta` (fallback pro
  endereço); `carregar_canais` lê e valida `rotulo` (texto). **O `rotulo` foi para o FIM do dataclass**
  (campos opcionais são posicionais em vários testes — pôr no meio quebrou a suíte; lição registrada).
- `persistencia/config_canais.py` (**novo**): `salvar_afericao` (grava pontos, remove ganho/offset
  linear órfãos), `salvar_rotulo`, `ler_pontos` — tudo via `tomlkit`, preservando comentários e os
  demais canais (helper `_editar_canal`).
- `dominio/regressao.py` + `dominio/erros.py`: **fix** — `ajustar_regressao` levanta
  `RegressaoIndeterminada` quando `var_x == 0` (tensão sem variação), em vez de `ZeroDivisionError`.
- `tomlkit>=0.13` em `dependencies` (core); `canais.exemplo.toml` documenta o `rotulo`.

**Frontend — `feat(apresentacao)` (commit `b2c8b56`):**
- `apresentacao/afericao.py` (**novo**, Presenter puro): `Afericao` — `adicionar_ponto`/
  `remover_ponto`/`definir_pontos`, `reta()` (captura `RegressaoIndeterminada` → None), `ganho_inverso()`
  (o "Ganho K" = V/un = 1/a), `correlacao_percentual()` ("100,00 %", BR), `aplicar()` persiste.
- `apresentacao/qt/janela.py`: `PainelAfericao` (`QDialog`) — tabela de pontos, **Ganho K** (V/un) +
  **Ganho 1/K** (un/V) + correlação espelhando o AqDados, botões **"Aplicar"/"Cancelar"** (texto
  próprio — os `StandardButton` do Qt vêm em inglês). `JanelaMonitor` ganhou: botão **Aferir…**,
  exibe **rótulo** na coluna "Sinal" (auto-ajustada) e nos seletores X/Y (endereço no `UserRole`/
  `itemData`), **edição de rótulo** na tabela (persiste via `salvar_rotulo`). A demo do Mac escreve
  numa **cópia de trabalho** do `canais.exemplo.toml` (`_demonstracao`), nunca no versionado.

**Docs — `docs` (commit `8918665`):** ADR-017; índice de ADRs (linha 017 + fio `013→015→016→017`);
roadmap (fatia 3 ✅, tara → fatia 4); CHANGELOG; CONTEXT (Nome do Sinal/rótulo/etiqueta); nota no
ADR-015 (tara movida); CLAUDE.md (range `adr/001…017`, árvore, stack); tarefas-futuras §3 fechada.

## 3.1 Desafios enfrentados e como resolvemos

1. **Adicionar campo no meio de um dataclass compartilhado quebrou a suíte.** Pôr `rotulo` entre
   `unidade` e `ganho` no `Canal` deslocou as construções **posicionais** em vários testes
   (`Canal("Mod1/ai0","tensao","kgf",100.0,0.0)` virou `rotulo=100.0`) → 9 falhas. **Resolução:**
   mover `rotulo` para o **fim** do dataclass (junto dos opcionais) e **rodar a suíte completa** após
   mexer em dataclass compartilhado (a regressão só apareceu fora dos testes de canais).
2. **Reabrir a aferição precisava dos pontos, mas o `Canal` só guarda a `reta`.** O canal por
   regressão descarta os pares `(V, valor)`. **Resolução:** os pontos vivem no **TOML** (fonte da
   verdade); `ler_pontos(caminho, canal)` relê de lá ao abrir o painel — sem inflar o `Canal` (evita
   um 2º significado para `Canal.pontos`, hoje = método segmento).
3. **Exibição (rótulo) × identidade (endereço) na tabela e nos combos.** A seleção usava
   `item.text()` como chave do canal — trocar o texto pelo rótulo quebraria a seleção e a edição.
   **Resolução:** identidade do canal no `UserRole` (tabela) / `itemData` (combos X/Y); o texto passou
   a ser o rótulo e ficou editável (renomear → `salvar_rotulo`).
4. **`ZeroDivisionError` ao montar a tabela com tensões iguais** (reportado pelo Weslley no terminal).
   Dois pontos de mesma tensão (ex.: `0→100`, `0→200`, comum antes de variar a tensão) faziam
   `ajustar_regressao` dividir por zero (`var_x == 0`), **abortando o `_sincronizar`** antes de
   atualizar os labels → sensação de "nada muda". **Resolução:** `RegressaoIndeterminada` no domínio;
   `Afericao.reta()` captura e retorna None (UI mostra `—` e Aplicar desabilitado); `carregar_canais`
   traduz para `ConfiguracaoInvalida` (config com volts todos iguais falha claro).
5. **Botões do Qt em inglês** ("Apply"/"Cancel"), violando português total. **Resolução:** botões com
   texto próprio "Aplicar"/"Cancelar" (não os `StandardButton`) + teste-guarda.
6. **Nomenclatura do ganho invertida vs. AqDados.** Nosso `reta.a` (un/V) é o "Ganho **1/K**" da tela
   do tio, não o "Ganho K"; e o offset `b` não aparecia. **Resolução:** exibir **Ganho K** (V/un =
   `1/a`, via `ganho_inverso()`) e **Ganho 1/K** (un/V = `a`) + correlação, espelhando o AqDados.
7. **A tara não tinha destino na UI.** Listada no painel pelo ADR-015, mas é por-ensaio (volátil) e
   exigiria estender o `MonitorAoVivo`. **Resolução:** **adiar para a fatia 4** (decisão no ADR-017),
   mantendo a fatia 3 na calibração persistida.

## 4. Estado atual

- **156 testes verdes** no Mac (`uv run pytest`), incl. smoke PySide headless (`offscreen`) e guardas
  de AST (`nidaqmx`/`PySide6`/`openpyxl`). Sem `nidaqmx`.
- **Validado na tela pelo Weslley** (5 screenshots): empilhamento por unidade, rótulos na tabela e
  nos seletores X/Y, XY Carga×Sg1 bico, aferição abrindo vazia (canal linear) e com pontos
  (ganho/correlação corretos), estados parado/adquirindo.
- **Working tree limpo** após os 3 commits (este handoff é o 4º commit da sessão).
- **Fatia 3 = FECHADA.**

## 5. Bloqueios e dependências

- **Push e merge são do Weslley** — a `develop` está **~13 commits à frente do `origin/develop`**
  (inclui as fatias 1–3 e docs). Confirmar/sincronizar antes de empilhar mais.
- **Backlog de tarefas-futuras majoritariamente bloqueado por dependência externa:** validar TXT-
  AqAnalysis (tio enviar TXT / Fase 5), sincronização start-trigger (só Windows), validação física
  (hardware do tio), FFT vs. não reescrever (precisa ADR-árbitro). O **nome do sinal (§3) foi feito**
  nesta fatia.

## 6. Próximos passos (escolher a frente — todas viáveis no Mac)

1. **Fatia 4 — Metadata + exportar pela UI + tara ao vivo** (a continuação natural, fecha a Fase 4):
   - cabeçalho do ensaio (obra, data, operador) no topo do workspace → rastreabilidade do laudo;
   - **exportar pela UI** reusando os exportadores (`csv-excel-br`, `xlsx`, `txt-aqanalysis`) com
     seleção de sinais e janela de tempo (já existem em `persistencia/exportadores/`);
   - **tara ao vivo:** estender o `MonitorAoVivo` para capturar o repouso (N amostras) e tarar os
     canais ao vivo (reusa `dominio.conversao.calcular_tara`); botão no widget. **Adiada da fatia 3
     de propósito** (ver ADR-017 Decisão 5).
2. **Tarefa futura — Ganho e Ponto de Referência:** 2º modo de aferição do AqDados (ADR-006 pendente).
3. **Tarefa futura — exportar ensaios gigantes pela entrada:** streaming no `carregar_csv` (ADR-012).
4. **TDD sempre:** começar pelo domínio/Presenter (Python puro, Mac); widget só desenha. Guardas
   intactas; commits separados por camada; **nada de commit/push/merge autônomo**.

## 7. Artefatos relevantes

- **Decisões:** [ADR-017](../adr/017-afericao-na-ui-e-escrita-de-config.md) (fatia 3),
  [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md) (plano de fatias, com a nota da tara),
  [ADR-006](../adr/006-calibracao-por-pontos.md) (regressão/correlação/tara),
  [referencia-lynx.md](../referencia-lynx.md) §1.2–1.3 (a tela de aferição espelhada).
- **Código (estenda na fatia 4):**
  - `src/ensaios_ni/apresentacao/afericao.py` — Presenter `Afericao` (calibração).
  - `src/ensaios_ni/apresentacao/monitor.py` — Presenter `MonitorAoVivo` (**a tara da fatia 4 entra
    aqui**; hoje `passo()` chama `converter(v, canal)` sem o argumento `tara=`).
  - `src/ensaios_ni/apresentacao/qt/janela.py` — `JanelaMonitor` + `PainelAfericao`.
  - `src/ensaios_ni/persistencia/config_canais.py` — escrita de TOML (tomlkit).
  - `src/ensaios_ni/persistencia/exportadores/` — exportadores prontos (reuso na fatia 4).
- **Interface nova (fatia 3):**
  ```python
  af = Afericao(caminho, canal, pontos=())     # pontos do TOML via ler_pontos(caminho, canal)
  af.adicionar_ponto(v, valor); af.remover_ponto(i); af.definir_pontos([...])
  af.reta()                  # Reta | None (None se <2 pontos ou tensão sem variação)
  af.ganho_inverso()         # "Ganho K" (V/un) = 1/reta.a | None
  af.correlacao_percentual() # "100,00 %" (BR) | "—"
  af.aplicar()               # salvar_afericao(caminho, canal, pontos) -> TOML
  ```
- **Comandos:**
  - `uv run pytest` → **156 passed** (confirma a base).
  - **Abrir o dashboard (Mac, com tela):** `PYTHONPATH=src uv run python -m ensaios_ni.apresentacao.qt.janela`
  - Demo escreve a config de trabalho em `$TMPDIR/ensaios-ni-canais.toml` (a aferição persiste lá).

## 8. Como iniciar a próxima sessão (fatia 4, no Mac)

1. Ler **este handoff** + [ADR-015](../adr/015-ux-e-fluxo-do-dashboard.md) (plano de fatias e estados)
   + [ADR-011](../adr/011-estrategia-de-exportacao.md)/[ADR-012](../adr/012-serie-temporal-e-exportadores.md)
   (exportadores) + [ADR-006](../adr/006-calibracao-por-pontos.md) (tara).
2. `uv run pytest` → **156 passed**. Se faltar PySide, `uv sync` instala o `[gui]`.
3. Confirmar com o Weslley se ele **deu push/mergeou** a `develop`; sincronizar se preciso.
4. **Decidir a frente** (§6 — provável fatia 4). Se fatia 4: começar pela **tara no `MonitorAoVivo`**
   (TDD, Presenter puro) e/ou pela **metadata + exportar pela UI** (reuso dos exportadores).
5. Regras de sempre: `import nidaqmx` só em `daqmx.py` (lazy); `import PySide6` só em
   `apresentacao/qt/` (guarda de AST); strain nunca usa defaults da API; português em tudo (inclusive
   textos de UI — os `StandardButton` do Qt vêm em inglês); commits separados por camada;
   **nada de commit/push/merge autônomo**.
