# Roadmap — ensaios-ni

Plano do início ao fim. O **critério de sucesso** não é "o código funciona" — é **o tio largar o
FlexLogger (pago) e usar o nosso software no trabalho real dele** (provas de carga e vibração em
estruturas), com confiança profissional. Toda fase é medida contra isso.

> Atualizado em 25/06/2026. As fases ganham detalhe conforme chegamos nelas — coisas novas vão
> aparecer durante a implementação (é esperado).

---

## Onde estamos

**Fim da Fase 3 (backend completo), entrando na Fase 4 (interface).** O software já lê, calibra,
grava e exporta — mas só por linha de comando. Falta a parte que o tio realmente vai tocar.

```
[0]──[1]──[2]──[3]── • ──[4]──[5]──[6]
 ✅    ✅    ✅    ✅   você   🔜    ⬜    ⬜
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

### Fase 4 — Interface gráfica (dashboard) 🔜 **a próxima, e a maior**

É o que transforma "funciona no terminal" em "o tio consegue usar". Software de aquisição é
**gráfico e em tempo real** (AqDados, FlexLogger, LabVIEW são todos assim). Subdivide em:

- **4.0 — Decisão de stack** (ADR): Plotly Dash vs React+FastAPI vs PyQt/pyqtgraph. Decisão do Weslley.
- **4.1 — Configurar & calibrar pela UI.** Tabela de canais e o painel de **aferição** (pontos +
  regressão + correlação + tara), espelhando o AqDados — sem editar TOML na mão.
- **4.2 — Visualização em tempo real.** O coração: ver o sinal **durante** o ensaio — sinal×tempo,
  **XY carga×deformação** (estático) e, no futuro, FFT ao vivo (vibração). Requisito do domínio.
- **4.3 — Controle do ensaio + metadata.** Iniciar/parar/duração, finito/contínuo, e dados do ensaio
  (obra, data, sensor, operador) para rastreabilidade do laudo.
- **4.4 — Exportar pela UI.** Reusa os exportadores que já existem.

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

- **Concluído:** Fases 0–3 (todo o backend: aquisição, calibração, exportação).
- **Faltam ~3 fases:** **4 (dashboard, a maior)**, 5 (validação física) e 6 (empacotamento & adoção).
- **Onde o esforço está:** a Fase 4 sozinha é provavelmente metade do trabalho restante — é onde o
  produto "ganha cara" para o tio.
- **É hora do dashboard?** Sim. O backend está maduro o suficiente para ter uma tela em cima dele, e
  a Fase 4 é o maior bloco entre nós e a adoção. O caminho certo é começar pelo **design/UX** (não
  sair codando tela): decidir a stack, depois desenhar o fluxo antes de implementar.
