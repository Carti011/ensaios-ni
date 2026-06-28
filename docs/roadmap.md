# Roadmap — ensaios-ni

Plano do início ao fim. O **critério de sucesso** não é "o código funciona" — é **o tio largar o
FlexLogger (pago) e usar o nosso software no trabalho real dele** (provas de carga e vibração em
estruturas), com confiança profissional. Toda fase é medida contra isso.

> Atualizado em 25/06/2026. As fases ganham detalhe conforme chegamos nelas — coisas novas vão
> aparecer durante a implementação (é esperado).

---

## Onde estamos

**Fase 4 (interface gráfica) concluída — as 4 fatias prontas.** O backend (Fases 0–3) faz o ciclo
ler → calibrar → gravar → exportar; agora o **dashboard** mostra o ensaio ao vivo (sinal×tempo
empilhado por unidade, XY carga×deformação, seleção de canais), deixa o tio **aferir pela tela**
(pontos → regressão → correlação, persistindo no `canais.toml`) com o **nome do sinal**, **tarar ao
vivo** (Zero Channel), **exportar** pela UI (Excel/CSV/TXT com seleção de sinais e janela de tempo)
e registrar a **metadata** do ensaio (obra/operador/data) num arquivo paralelo `.meta.toml`. Próximo:
a **validação física** no hardware do tio (Fase 5).

```text
[0]──[1]──[2]──[3]──[4]──[5]──[6]
 ✅    ✅    ✅    ✅    ✅    ⬜    ⬜
                          você
                          aqui
```

---

## Fases concluídas ✅

- **Fase 0 — Ambiente (Windows).** NI-DAQmx + NI-MAX, dispositivos simulados (9184 + 2×9205 + 9235).
- **Fase 1 — Prova de vida.** Ler tensão/strain dos simulados; confirmar a API do `nidaqmx`.
- **Fase 2 — Aquisição (backend).** Porta/adaptador, tensão (9205) + strain (9235), modos finito e
  contínuo, gravação CSV. **Validada no Windows simulado** (25/06). Falta o número físico (Fase 5).
- **Fase 3 — Conversão & Exportação (backend).** Calibração por regressão/segmento/linear +
  correlação + tara; exportadores CSV-Excel-BR, `.xlsx` e TXT-AqAnalysis (provisório) com seleção de
  sinais e janela de tempo; CLI. *(O plano antigo juntava "dashboard" nesta fase; ele é grande demais
  e virou fase própria.)*

**Resultado até aqui:** um software de **linha de comando** que faz o ciclo completo
ler → calibrar → gravar → exportar. Suficiente para o Weslley validar; **não** para o tio usar.

---

## Fases que faltam ⬜

### Fase 4 — Interface gráfica (dashboard) ✅ **concluída (28/06) — a maior**

É o que transforma "funciona no terminal" em "o tio consegue usar". Stack decidida:
**PySide6 + pyqtgraph** ([ADR-013](adr/013-stack-do-dashboard.md), binding fixado no
[ADR-015](adr/015-ux-e-fluxo-do-dashboard.md)). UX e plano de **fatias verticais** no ADR-015:

- **Fatia 1 — Monitor ao vivo** ✅ (26/06). Workspace de painéis; o `fake` transmite → sinal×tempo
  correndo → Parar grava CSV. Presenter `MonitorAoVivo` (Python puro) + Widget PySide6 fino.
- **Fatia 2 — XY + multicanal** ✅ (27/06). Empilhamento por unidade, **XY carga×deformação** e
  seleção de canais (checkbox) com recolhimento de sub-plot vazio
  ([ADR-016](adr/016-visualizacao-do-dashboard.md)).
- **Fatia 3 — Aferição na UI** ✅ (27/06). Tabela de canais editável + painel de aferição
  (pontos + regressão + correlação), espelhando o AqDados, **persistindo no `canais.toml`** com
  `tomlkit` (preserva comentários; o `tomllib` é só leitura). Inclui o **nome do sinal** (`rotulo`/
  `etiqueta`). A **tara** foi adiada para a fatia 4 (é por-ensaio) — ver
  [ADR-017](adr/017-afericao-na-ui-e-escrita-de-config.md).
- **Fatia 4 — Metadata + exportar + tara** ✅ (28/06). Campos de metadata no topo (obra/operador/
  data/obs.) salvos num `<ensaio>.meta.toml` paralelo ([ADR-018](adr/018-metadata-do-ensaio.md)) e
  carimbados no laudo exportado; **exportar pela UI** reusando os exportadores (Excel/CSV/TXT, com
  seleção de sinais e janela de tempo); e a **tara ao vivo** (Zero Channel) estendendo o
  `MonitorAoVivo`.

### Fase 5 — Validação física no hardware do tio

- Trocar nomes simulados pelos reais; a leitura tem que **bater com o test panel do NI-MAX**.
- Calibrar a extensometria de verdade (o **número físico** do strain — pendente desde a Fase 2).
- Validar o **TXT** importando no AqDAnalysis dele (ver `docs/tarefas-futuras.md`).
- Rodar o **fluxo completo** num ensaio de teste, na casa dele.

### Fase 6 — Empacotamento & adoção (o "dar certo")

- **Distribuição amigável:** o tio não roda `pip install`. Precisa de um executável/instalador
  Windows (ex.: PyInstaller → `.exe`) ou um caminho de instalação muito simples.
- **Robustez de longa duração:** ensaios de meses exigem recuperação de queda de rede e rotação de
  arquivo (hoje só anotado nos ADRs 007/012).
- **Polimento:** mensagens de erro amigáveis, guia de uso para o tio.
- **Adoção real:** o tio usar num ensaio de verdade → feedback → iterar. Sucesso = ele largou o
  FlexLogger.

---

## Resumo executivo

- **Concluído:** Fases 0–4 (todo o backend + o dashboard completo: monitor ao vivo, XY/multicanal,
  aferição, tara, exportar e metadata pela UI).
- **Faltam 2 fases:** 5 (validação física no hardware do tio) e 6 (empacotamento & adoção).
- **Onde o esforço está:** o dashboard (a maior fatia) está pronto e roda no Mac com o `fake`. O que
  separa o tio de usar é levar isso ao **hardware real** (Fase 5) e empacotar num `.exe` (Fase 6).
- **Próximo passo:** a **validação física** (Fase 5) — trocar os nomes simulados pelos reais, bater a
  leitura com o test panel do NI-MAX e calibrar a extensometria de verdade, na casa do tio.
