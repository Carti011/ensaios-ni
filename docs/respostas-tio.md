# Respostas do dono do hardware — ensaios-ni

Registro do que o dono do equipamento (tio do Weslley) informou sobre o setup físico dos ensaios. É a **fonte de verdade para o futuro `config/canais.toml`** e para a configuração das tasks de aquisição. Atualizar a cada rodada de perguntas.

> **Atualização 22/06/2026:** a rodada 2 foi respondida (2 áudios). Os bloqueios 🔴 caíram. A grande revelação: a conversão **não é uma fórmula linear fixa** — o dono trabalha com **calibração empírica por pontos + tara (null)**, como o AqDados da Lynx faz. Isso vira [ADR-006](adr/006-calibracao-por-pontos.md) e revisa o [ADR-002](adr/002-conversao-linear-e-contrato-da-porta.md).

---

## Placar

| Frente | O que precisamos | Status |
| ------ | ---------------- | ------ |
| Divisão dos módulos | qual é strain, quais são tensão | ✅ 9235 strain; 2× 9205 tensão |
| Excitação no 9205 | os módulos de tensão fornecem excitação? | ✅ não fornecem (sensores alimentados por fora) |
| Rede | topologia e tipo de IP | ✅ direto no PC, IP fixo (número no cofre privado) |
| Amostragem (vibração) | taxa em Hz | ✅ 1024 Hz (acelerômetro) |
| Amostragem (carga × deformação) | taxa dos ensaios lentos | ✅ **20 Hz** (estático), confirmado pelo dono |
| 9235 — gage factor | fator do extensômetro | ✅ **2,14–2,16, varia por lote** (configurável) |
| 9235 — ponte/resistência | 120 Ω em quarter-bridge | ✅ etiqueta + voz; cabo longo = **3 fios, 22 AWG** |
| 9235 — canais | quantos e o que medem | 🟡 varia por obra; não há número fixo |
| 9205 — conversão | volts→unidade por canal | ✅ **calibração por pontos + tara** (ver ADR-006) |
| 9205 — canais | que sensor em cada canal | ✅ LVDT, acelerômetro (alim. externa); célula de carga em dúvida |
| 9205 — fiação | diferencial ou single-ended | ✅ **diferencial** (dono confirmou a recomendação) |
| Acelerômetro | marca/modelo e sensibilidade | ✅ **Dytran 7523A1** — 550 mV/g, ±2g, 0–1500 Hz, 5 V DC, triaxial |
| Ensaio | duração e o que é "resultado" | ✅ de 1 h a **1 ano contínuo** → exige aquisição contínua |

---

## Rodada 2 — respondida 22/06/2026 (2 áudios)

Transcrito local com `mlx-whisper` (`large-v3-turbo`). Trechos óbvios corrigidos.

### Áudio 1 — sobre o software (grátis × pago)

> "Que top! Na verdade você tá lendo um canal flutuante, e colocou os módulos, as placas, simulando aqui as placas. Esse programa aí é o **NI-MAX**. Tem o **FlexLogger** que dá pra acessar e começar a mexer. Esse aí, FlexLogger, **é o que você precisa criar** — pra não ficar refém, senão eu vou ter que **pagar assinatura** pra esses caras do FlexLogger."

**Leitura:** o dono entende o objetivo certo. A pilha NI: **NI-DAQmx (driver, grátis)** + **NI-MAX (grátis)** já fazem o hardware funcionar; o único pago é o **FlexLogger** (assinatura) — e é exatamente a camada que este projeto reescreve. **Ele não precisa pagar nada** para o hardware funcionar.

### Áudio 2 — respostas técnicas

- **Gage factor (9235):** quarter-bridge, 120 Ω, **fator varia entre 2,14 e 2,16** ("sempre variando", depende do lote do extensômetro). → tem de ser **parâmetro configurável por canal/ensaio**, nunca fixo.
- **Conversão (o método real dele):** não há fórmula fixa. Ele liga o sensor, lê a tensão atual e **declara aquele ponto como zero (null/tara)**; para strain, lê e **multiplica por 1.000.000 → microstrain**. Para os demais sensores, "a correlação voltagem→engenharia **depende de cada sensor**" → ele monta uma **planilha/painel de calibração**: aplica carga conhecida, registra a voltagem e **vai construindo a curva ponto a ponto** (igual o canal de calibração do AqDados/Lynx). Disse: "no NI-DAQmx eu não sei como faz essa curva." → **oportunidade do projeto.**
- **Cabos (9235):** cabo longo → **3 vias, 22 AWG** (three-wire quarter-bridge, p/ compensar resistência). Varia por obra (às vezes curto, às vezes longo).
- **Célula de carga:** usa também, "mas **nessa placa parece que não liga** a célula de carga, não sei se dá certo" (dúvida dele — célula de ponte precisa de excitação que o 9205 não fornece).
- **9205 — sensores:** **LVDT** (deslocamento) e **acelerômetro** (excitado por **5 V de alimentação externa**, já que a placa não excita). Também cita pressão (**MPa**) e carga (**kgf**) como grandezas de saída.
- **Vibração:** medida com **acelerômetro**, sensibilidade **2G**, a **1024 Hz**.
- **Duração:** "depende — de **uma hora a um mês contínuo, ou um ano**; prova de carga 24 h." → monitoramento de **longa duração** é requisito real.
- **IP fixo:** respondeu o número (registrado no **cofre privado**, não versionado).

### Consequências para o software

- **Revisar a conversão:** o [ADR-002](adr/002-conversao-linear-e-contrato-da-porta.md) (linear `ganho·V+offset` fixo em config) é insuficiente. O modelo real é **calibração por pontos + tara** → [ADR-006](adr/006-calibracao-por-pontos.md). O linear vira caso particular (2 pontos).
- **Aquisição contínua de longa duração** → [ADR-007](adr/007-aquisicao-continua.md). A leitura finita atual (lê N e para) não cobre monitoramento de meses.
- **Task de strain (fatia futura):** quarter-bridge 120 Ω, **3 fios**, gage factor 2,14–2,16 configurável, conversão para **microstrain**, com **null** inicial.
- **Compatibilidade Lynx:** AqDados (aquisição/calibração/gravação) e AqDAnalysis (tempo/frequência/filtros/relatórios) são a referência funcional. Vale alinhar o formato de arquivo para abrir nos dois.

---

## Estudo de mercado (23/06/2026) — respostas obtidas sem o tio

A pesquisa (FlexLogger/DAQmx + docs NI/Lynx + site da OFM) fechou o **comportamento** do software
e respondeu boa parte da rodada 3. Detalhe e fontes em [referencia-flexlogger.md §5](referencia-flexlogger.md).
Resumo do que **já sabemos** (não precisa perguntar, só confirmar):

| Tema | Resposta da pesquisa | Confiança |
| ---- | -------------------- | --------- |
| Acelerômetro (marca) | **Dytran (EUA)**, triaxial, sub-mg (site OFM) — "de tram" = Dytran | alta |
| Fiação 9205 | **diferencial** (par trançado blindado; padrão NI p/ campo) | alta (recomendação) |
| Taxa ensaios lentos | estático ~**0,02–10 Hz** (1 Hz típico / por estágio); dinâmico já é 1024 Hz | média |
| Fora da faixa | **clamp** (DAQmx clipa na leitura); outliers = análise depois | alta |
| Célula de carga no 9205 | não liga direto; precisa **condicionador externo com saída em tensão** | alta |
| Formato AqDAnalysis | importa **proprietário** (Lynx/Catman .BIN/MGCPlus .MEA/MTS); troca via **TXT**, não CSV | alta |
| Tara | prática padrão ("Zero Channel"); repouso de **alguns segundos** | média |

**Implicação nova:** paridade direta de **arquivo** com o AqDAnalysis é improvável (formatos
proprietários). Caminho realista: CSV/TXT legível + nossa própria análise no futuro.

## Rodada 3 — respondida (parcial) 23/06/2026

O dono respondeu **"tá tudo certo"** + um dado de taxa + a foto do acelerômetro. O "tá tudo certo"
**valida as inferências da pesquisa** (fiação diferencial, clamp fora da faixa, tara, célula com
condicionador em tensão, formato de arquivo). Dados concretos:

- **Taxa dos ensaios estáticos: 20 Hz.** (A pesquisa estimou 0,02–10 Hz; o real é 20 Hz — baixa
  comparada aos 1024 Hz da vibração, como esperado.)
- **Acelerômetro: Dytran 7523A1** (S/N 3218). Especificações oficiais (datasheet):
  - **Sensibilidade 550 mV/g** → conversão `g = volts / 0,550` (ganho ≈ **1,818 g/V**); é canal de
    **tensão** no 9205.
  - **Faixa ±2g**, frequência **0–1500 Hz** (X/Y; cobre os 1024 Hz da vibração).
  - **Triaxial, DC-response (capacitivo)**, alimentação **5 V DC**, saída em tensão — confere com o
    "acelerômetro alimentado por 5 V externos" do áudio. Liga direto no 9205.

**O dono não vai detalhar o resto agora.** Por decisão do Weslley (23/06), as demais perguntas
ficam **encerradas** — o que faltar segue **boas práticas pesquisadas** (ver abaixo), e novas
perguntas só quando surgir necessidade real. Nada disso bloqueia o backend.

## Rodada 3 — encerrada (23/06/2026): decisões por boas práticas

As perguntas que o dono não respondeu **não ficam pendentes**. Seguimos os melhores parâmetros
pesquisados (FlexLogger/NI/Lynx — ver [referencia-flexlogger.md](referencia-flexlogger.md)), com
responsabilidade. Decisões adotadas (revisáveis quando ele detalhar):

- **LVDT, pressão, célula de carga:** canais de **tensão** no 9205, conversão por **calibração de
  pontos** (o método do próprio dono) ou linear — preenchidos no `canais.toml` quando o modelo de
  cada sensor aparecer. Não precisa fixar número agora.
- **Célula de carga:** via condicionador com **saída em tensão** (padrão NI); calibrada por pontos
  (a OFM já calibra com rastreabilidade INMETRO/RBC).
- **Nº de pontos de calibração:** suportamos N (≥ 2) — o dono usa quantos quiser.
- **Formato de arquivo: CSV legível.** O AqDAnalysis não importa CSV de terceiros; substituímos o
  **FlexLogger**, não o AqDAnalysis. Análise própria (FFT etc.) fica para fase futura.
- **Fiação 9205: diferencial.** **Tara:** padrão "Zero Channel", janela de repouso parametrizável
  (`--amostras-tara`). **Taxa estático: 20 Hz** (confirmada).

Novas perguntas ao dono só quando realmente surgir necessidade.

---

## Rodada 4 — 23/06/2026 (prints dos softwares + qual copiar)

O dono enviou prints (WhatsApp) do **AqDados**, do **AqDAnalysis** e do **FlexLogger**, com as
seguintes mensagens (transcrição literal):

> - "Essas são as fotos do AqDAnalisis"
> - "Essas fotos são do AqDados"
> - "Se for para copiar um programa o ideal seria o **AqDados e AqDAnalisis juntos**, este seria o
>   melhor dos mundos"
> - "Pq **eu já domino**"
> - "Já o **flexlogger, estou aprendendo a mexer agora**."
> - "Não está conectada mais, esse aí é o flexlogger"
> - "O **AqDAnalisis só exporta txt** e o arquivo de gravação do **AqDados usa a extensão .LDT** e
>   **só o AqDAnalisis abre** este tipo de arquivo, que eu saiba."

### Consequências (decisões do Weslley, 24/06/2026)

- **Vira o norte de paridade.** O espelho de produto passa do FlexLogger para o **Lynx (AqDados +
  AqDAnalysis)**, que o dono domina → [ADR-010](adr/010-paridade-com-o-lynx.md). O FlexLogger fica
  só como referência técnica do driver (ADR-008 parcialmente substituído).
- **Estratégia de arquivo definida.** Não geramos `.LDT` (proprietário). Interoperamos exportando
  **TXT** que o AqDAnalysis importa → [ADR-011](adr/011-estrategia-de-exportacao.md). **Não
  reescrevemos** a suíte de análise da Lynx — o dono analisa lá.
- **Descobertas técnicas** das telas (calibração por regressão + correlação, balanço/repouso, shunt
  cal, unidades µm/m e mm/s², nomes reais de canais) registradas em
  [referencia-lynx.md](referencia-lynx.md).
- **Privacidade:** os prints contêm nomes de clientes/obras e o nome do dono → **não versionados**
  no repositório; só a análise textual fica no projeto.

---

## Rodada 1 — 21/06/2026 (histórico)

Confirmado: 9235 só strain; 2× 9205 só tensão (sem excitação); chassi direto no PC com IP fixo; vibração a 1024 Hz. Transcrições e detalhes preservados no histórico do git (commit `db48757`+).
