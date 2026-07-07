# Roadmap — ensaios-ni

Plano do início ao fim. O **critério de sucesso** não é "o código funciona" — é **o tio largar o
FlexLogger (pago) e usar o nosso software no trabalho real dele** (provas de carga e vibração em
estruturas), com confiança profissional. Toda fase é medida contra isso.

> Atualizado em 04/07/2026. As fases ganham detalhe conforme chegamos nelas — coisas novas vão
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
leitura de tensão ao vivo na aferição** (o "Leitura do A/D", pedido direto do tio). Ainda em 01/07, a
aferição ganhou **robustez e feedback** (alerta de correlação baixa) e a **Fase 6 arrancou**: o
**`.exe` foi buildado e validado no Windows do dev** — abre a tela inicial e monta o dashboard, sem
console ([ADR-022](adr/022-empacotamento-exe-pyinstaller.md)). Em **02/07**, a aquisição ganhou
**mensagens de erro amigáveis** (driver ausente, chassi/rede fora, canal inexistente — o tio entende o
que fazer, sem traceback) e montou-se o **pacote de distribuição** ([docs/pacote-tio/](pacote-tio/README.md)):
guia de build, `LEIA.txt` para o tio e o `canais.toml` pronto (1 canal de strain — o cenário da ida).
Ainda em **02/07**, o `.exe` foi buildado no Windows do dev e o **`Iniciar` foi validado no simulado
do NI-MAX**: a aquisição empacotada, exercitada pela primeira vez, expôs um bug de metadata do
PyInstaller (`nidaqmx`/`nitypes` leem a própria versão em runtime e o `.dist-info` não ia no bundle),
corrigido com `copy_metadata` no `.spec` ([ADR-022](adr/022-empacotamento-exe-pyinstaller.md)); depois
do fix o gráfico correu contra o driver simulado (aquisição real pela arquitetura). **Correção de
03/07:** o simulado roda mesmo com o **NI-MAX fechado** — a antiga nota do "fechar o NI-MAX derruba a
leitura" era enganosa (ver [ADR-022](adr/022-empacotamento-exe-pyinstaller.md)).
Em **04/07** o tio fez um **teste de campo** (leu a deformação, funciona) e, no **levantamento de
requisitos** (imagens + áudios), destravou duas frentes: o **erro recorrente ao gravar** ganhou causa —
**DAQmx `-200279` (buffer overrun** na aquisição contínua), com a tradução amigável a corrigir — e o
pedido de **ler em voltagem/V/V e correlacionar** foi reforçado (evidenciado pelo FlexLogger dele, que
mostra ε + mV/V). Pediu também **filtro de ruído** no sinal ao vivo (**feito**: média móvel de visualização no gráfico,
sem afetar o CSV). Detalhe e demais requisitos em [tarefas-futuras.md](tarefas-futuras.md).

Em **07/07** o Weslley **validou o Windows** (dispositivos simulados no NI-MAX): git sincronizado,
suíte verde, `.exe` builda, aquisição finita/contínua e export `xlsx` via CLI sem erro (o fix do
`-200279` não regrediu o streaming — `tempo_s` contínuo através das fronteiras de bloco). Testando o
**editor de canais** no Windows, apareceu um **crash**: adicionar um canal sem a conversão (ganho/offset
nem pontos) **gravava mesmo assim** e derrubava o app ao reabrir o perfil — **corrigido por TDD** (o
editor valida pela regra do domínio **antes** de gravar e lê o perfil de forma **tolerante**; refina a
decisão 4 do [ADR-023](adr/023-configuracao-de-canais-na-ui.md)). Ainda em 07/07: **botão "Abrir
ensaio"** na tela inicial (abre o dashboard do selecionado sem duplo-clique) e a **janela de exportação**
ganhou **duração legível + trecho opcional + `hh:mm:ss`** (o tio não pensa em segundos; módulo puro
`apresentacao/tempo.py`). Tudo na `develop`; **PR #12** aberta (`develop → main`, aguardando o merge do
Weslley). **315 testes no Mac.**

Faltam os **ajustes finos** da Fase 5, todos dependentes do hardware/Windows do tio (não bloqueiam o
"funciona"): a comparação numérica com o test panel do NI-MAX (na mesma unidade, por **variação**
carregado−repouso) e validar o **TXT** no AqDAnalysis do tio. Na Fase 6, o `.exe` já **abre e adquire
no simulado** (02/07); falta o **Iniciar no hardware real do tio** (driver + chassi) e o polimento
restante (robustez de longa duração;
as **mensagens de erro amigáveis já foram feitas** em 02/07). Em **04/07** a **Parte A do
[ADR-023](adr/023-configuracao-de-canais-na-ui.md) (configuração de canais na UI) foi concluída**:
biblioteca de perfis, editor de canais e gerência completa (criar/importar/renomear/remover/duplicar/
exportar), tudo pela tela — tira do tio a edição manual do `.toml`. Restam dela a **Parte B**
(discovery de dispositivos, só no Windows) e refinamentos menores. O **levantamento de requisitos do
tio** (04/07) já foi feito e destravou o fix do editor, o botão e a exportação (07/07). As **próximas
frentes estruturais** são o **ADR-024 (ler o V/V do strain)** e, quando o tio responder sobre ensaios
de dias/meses, um **ADR de estratégia de arquivo** (rotação/TDMS + concatenação no AqDAnalysis); depois,
a Fase 7 (FFT ao vivo) e as pendências de [tarefas-futuras.md](tarefas-futuras.md).

```text
[0]──[1]──[2]──[3]──[4]──[5]──[6]──[7]
 ✅    ✅    ✅    ✅    ✅    🟡    🟡    ⬜
                          você aqui
                       (5 no tio, 6 o .exe)
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
- **Configuração de canais na UI ([ADR-023](adr/023-configuracao-de-canais-na-ui.md)):** o tio não
  edita `.toml` à mão — biblioteca de **perfis** por obra (salvos numa pasta do app, editáveis) +
  **editor de canais** na tela e, depois, **discovery** dos canais do equipamento. Fatiado: **Parte A**
  (perfis + editor) roda no **Mac** e é a **próxima frente de desenvolvimento**; **Parte B** (discovery)
  espera o Windows/feedback. Remove o último passo manual entre "recebeu o `.exe`" e "está adquirindo".
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
- **Faltam 3 fases:** 5 (validação física), 6 (empacotamento & adoção — inclui a **configuração de
  canais na UI**, [ADR-023](adr/023-configuracao-de-canais-na-ui.md)) e 7 (paridade dinâmica — FFT ao
  vivo, [ADR-021](adr/021-fft-ao-vivo-paridade-dinamica.md)).
- **Onde o esforço está:** o dashboard (a maior fatia) está pronto e roda no Mac com o `fake`. O que
  separa o tio de usar é levar isso ao **hardware real** (Fase 5) e empacotar num `.exe` (Fase 6).
- **Reavaliação de rota (01/07):** as últimas sessões foram features no Mac; a direção volta ao que o
  [ADR-019](adr/019-foco-em-validacao-fisica-e-adocao.md) mandou — **adoção acima de features**. A
  frente ativa é o **`.exe`** (bloqueador nº 1: o tio ainda não consegue abrir o programa); a
  validação numérica + TXT dependem de uma ida ao tio; o FFT ao vivo (Fase 7) fecha a paridade no
  dinâmico depois disso.
