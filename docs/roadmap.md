# Roadmap — ensaios-ni

Plano do início ao fim. O **critério de sucesso** não é "o código funciona" — é **o tio largar o
FlexLogger (pago) e usar o nosso software no trabalho real dele** (provas de carga e vibração em
estruturas), com confiança profissional. Toda fase é medida contra isso.

> Atualizado em 28/06/2026. As fases ganham detalhe conforme chegamos nelas — coisas novas vão
> aparecer durante a implementação (é esperado).

---

## Onde estamos

**Fase 5 (validação física) em andamento — validada FUNCIONALMENTE no hardware real do tio
(29/06/2026).** O software leu o **NI 9235 real** e respondeu corretamente à deformação aplicada
(força numa chapa com o gage → gráfico coerente com a direção da força): confirma que reconhece a
DAQ, recebe o sinal do sensor e reage. Era o objetivo da ida. As Fases 0–4 (backend completo +
dashboard) já estavam prontas. Em 30/06 o **gage factor** passou a vir do `canais.toml`, por canal
([ADR-020](adr/020-parametros-de-strain-por-canal.md)). Em **01/07** fecharam três frentes no Mac: o
**launcher do dashboard com hardware real** (`qt.hardware`, sobre o `AdaptadorDaqmx`), a **tela
inicial** de abertura sem CLI (o "Abrir configuração…", pré-requisito do `.exe`) e a **captura da
leitura de tensão ao vivo na aferição** (o "Leitura do A/D", pedido direto do tio). **203 testes no
Mac.**

Faltam os **ajustes finos** da Fase 5, todos dependentes do hardware/Windows do tio (não bloqueiam o
"funciona"): a comparação numérica com o test panel do NI-MAX (na mesma unidade, por **variação**
carregado−repouso) e validar o **TXT** no AqDAnalysis do tio. Depois, a Fase 6 (`.exe`).

```text
[0]──[1]──[2]──[3]──[4]──[5]──[6]──[7]
 ✅    ✅    ✅    ✅    ✅    🟡    ⬜    ⬜
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

### Fase 6 — Empacotamento & adoção (o "dar certo") — **frente ativa (01/07)**

- **Distribuição amigável:** o tio não roda `pip install`. Precisa de um executável/instalador
  Windows (ex.: PyInstaller → `.exe`) ou um caminho de instalação muito simples. **É o bloqueador
  nº 1 da adoção: hoje o programa não abre na máquina dele.** Entrypoint do `.exe` = a tela inicial
  sem CLI (`qt.hardware`).
- **Robustez de longa duração:** ensaios de meses exigem recuperação de queda de rede e rotação de
  arquivo (hoje só anotado nos ADRs 007/012).
- **Polimento:** mensagens de erro amigáveis, guia de uso para o tio.
- **Adoção real:** o tio usar num ensaio de verdade → feedback → iterar. Sucesso = ele largou o
  FlexLogger.

### Fase 7 — Paridade dinâmica: FFT ao vivo ([ADR-021](adr/021-fft-ao-vivo-paridade-dinamica.md))

- **Decisão de escopo (01/07):** substituir o FlexLogger **também no dinâmico** — espectro de
  frequência ao vivo no dashboard (o "Frequency Graph"). A análise pesada (fadiga, Rainflow,
  relatórios) segue no AqDAnalysis via TXT ([ADR-011](adr/011-estrategia-de-exportacao.md)).
- Vem **depois** da Fase 6: é paridade, não pré-requisito de o tio abrir o programa.

---

## Resumo executivo

- **Concluído:** Fases 0–4 (todo o backend + o dashboard completo: monitor ao vivo, XY/multicanal,
  aferição, tara, exportar e metadata pela UI).
- **Faltam 3 fases:** 5 (validação física), 6 (empacotamento & adoção) e 7 (paridade dinâmica —
  FFT ao vivo, [ADR-021](adr/021-fft-ao-vivo-paridade-dinamica.md)).
- **Onde o esforço está:** o dashboard (a maior fatia) está pronto e roda no Mac com o `fake`. O que
  separa o tio de usar é levar isso ao **hardware real** (Fase 5) e empacotar num `.exe` (Fase 6).
- **Reavaliação de rota (01/07):** as últimas sessões foram features no Mac; a direção volta ao que o
  [ADR-019](adr/019-foco-em-validacao-fisica-e-adocao.md) mandou — **adoção acima de features**. A
  frente ativa é o **`.exe`** (bloqueador nº 1: o tio ainda não consegue abrir o programa); a
  validação numérica + TXT dependem de uma ida ao tio; o FFT ao vivo (Fase 7) fecha a paridade no
  dinâmico depois disso.
