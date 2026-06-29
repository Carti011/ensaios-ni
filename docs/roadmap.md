# Roadmap — ensaios-ni

Plano do início ao fim. O **critério de sucesso** não é "o código funciona" — é **o tio largar o
FlexLogger (pago) e usar o nosso software no trabalho real dele** (provas de carga e vibração em
estruturas), com confiança profissional. Toda fase é medida contra isso.

> Atualizado em 28/06/2026. As fases ganham detalhe conforme chegamos nelas — coisas novas vão
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
- **Fase 4 — Interface gráfica (dashboard), a maior.** Concluída em 28/06. Workspace **PySide6 +
  pyqtgraph** ([ADR-013](adr/013-stack-do-dashboard.md)/[ADR-015](adr/015-ux-e-fluxo-do-dashboard.md))
  em 4 fatias verticais: (1) monitor ao vivo; (2) XY carga×deformação + empilhamento por unidade +
  seleção de canais; (3) aferição na UI (pontos → regressão → correlação, persistindo no `canais.toml`)
  com nome do sinal; (4) metadata do ensaio + exportar pela UI + tara ao vivo. **178 testes verdes** no
  Mac, com o adaptador `fake`.

**Resultado até aqui:** o ciclo completo — ler → calibrar → gravar → exportar — roda tanto pela **CLI**
quanto por um **dashboard** que mostra o ensaio ao vivo. Tudo testado no Mac com o `fake`. O que falta
não é software no Mac: é levar ao **hardware real** e empacotar para o tio usar.

---

## Fases que faltam ⬜

### Fase 5 — Validação física no hardware do tio

- Trocar nomes simulados pelos reais; a leitura tem que **bater com o test panel do NI-MAX**.
- Calibrar a extensometria de verdade (o **número físico** do strain — pendente desde a Fase 2).
- Validar o **TXT** importando no AqDAnalysis dele (ver `docs/tarefas-futuras.md`).
- Rodar o **fluxo completo** num ensaio de teste, na casa dele.

> Passo a passo completo, do ambiente ao ensaio validado: [guia-teste-hardware.md](guia-teste-hardware.md).

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
