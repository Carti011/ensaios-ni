# Referência — Lynx (AqDados + AqDAnalysis), o software que o dono domina

Análise das telas que o dono do hardware enviou (WhatsApp, 23/06/2026): prints do **AqDados**
(aquisição/calibração) e do **AqDAnalysis** (análise), além do **FlexLogger** para comparação.

> **Por que esta referência existe.** O dono disse, textualmente: *"Se for para copiar um programa
> o ideal seria o AqDados e AqDAnalisis juntos... porque eu já domino. Já o FlexLogger, estou
> aprendendo a mexer agora."* Logo, o **modelo mental, o vocabulário e o fluxo de trabalho** que o
> nosso software deve espelhar são os do **Lynx**, não os do FlexLogger. Esta é a nova fonte de
> verdade de paridade de UX. Ver [ADR-010](adr/010-paridade-com-o-lynx.md). O FlexLogger continua
> útil só como referência técnica de baixo nível (por baixo é o mesmo NI-DAQmx) —
> ver [referencia-flexlogger.md](referencia-flexlogger.md).

> **Não é para copiar o visual.** As telas são de uma geração antiga de UI (Windows clássico).
> O que se herda é o **comportamento, o vocabulário e a organização das tarefas**, com UX própria
> e moderna. As imagens originais **não são versionadas** no repositório (contêm nomes de clientes
> e obras do dono); só esta análise textual fica no projeto.

---

## 1. AqDados — aquisição e calibração

Software de aquisição multicanal (versão vista: **7.02.31**). É a referência direta do nosso
backend de aquisição + conversão.

### 1.1 Configuração das Entradas Analógicas (tabela de canais)

Tela central: uma **tabela com uma linha por canal**. Colunas observadas:

| Coluna | O que é | Equivalente no nosso projeto |
| ------ | ------- | ---------------------------- |
| Canal / CN Mod | índice do canal no módulo (checkbox liga/desliga) | nome do canal físico (`Mod1/ai0`) |
| **Nome do Sinal** | rótulo humano do canal | nome lógico no `canais.toml` |
| **Unidade** | unidade de engenharia | unidade no `canais.toml` |
| **Tipo** | tipo de conversão: `PT100`, `Linear`, … | tipo de escala (linear/pontos) |
| Faixa do A/D | faixa de entrada (`±10 V`) | faixa de aquisição |
| Lim. Inferior / Lim. Superior | limites da escala | limites de clamp |
| Descrição | texto livre | — |

**Nomes e unidades reais do dono** (confirmam o domínio):

- `Temperatura` → tipo **PT100** → unidade **°C / OHM**.
- `Sg1 bico`, `Sg2 reforço`, `Sg3 reforço` → strain → unidade **µm/m** (microstrain).
- `Ac02x/y/z`, `Ac03x/y/z`, `Ac04x/y/z` → três **acelerômetros triaxiais** → unidade **mm/s²**.

Lições: os canais têm **nome físico significativo** ("bico", "reforço" = local da peça); a unidade
é **por canal**; o `Tipo` inclui curvas prontas de sensor (PT100), não só linear.

### 1.2 Aferição (= calibração) — menu "Aferir"

O AqDados oferece **três caminhos** no menu `Aferir`:

1. **por Regressão Linear…**
2. **por Ganho e Ponto de Referência…**
3. **Leitura do A/D**

Isso refina o [ADR-006](adr/006-calibracao-por-pontos.md): o método do dono não é só "tabela de
pontos com interpolação"; ele tem **dois modos distintos** de derivar a escala.

### 1.3 Tela "Aferição por Regressão Linear"

É o equivalente direto da nossa calibração por pontos, com detalhes que **não tínhamos previsto**:

- **Tabela de pontos** `(V, Val. Eng.)` com botões **Inserir / Remover / Copiar**. Exemplo real
  (canal PT100): `(1,2241 → 101)`, `(1,4569 → 119)`, `(2,6770 → 217)`.
- **Ganho K** e **Ganho 1/K** derivados dos pontos (`0,01250017 V/OHM` / `79,99889 OHM/V`).
- **Correlação: 100,00 %** — mede a **qualidade do ajuste** da reta aos pontos. Indicador novo,
  que vale exibirmos: dá ao usuário confiança de que a calibração está boa.
- **Limites Especificados** vs **Limites Calculados** (faixa em V e na unidade).
- Botão **"Aceita Limites Calculados"**.

**Diferença técnica importante (ponto a refinar no ADR-006):** "Regressão Linear" ajusta **uma
única reta a N pontos** (mínimos quadrados, daí a correlação), enquanto o nosso ADR-006 hoje faz
**interpolação linear por segmento** (a reta passa exatamente por cada ponto). São métodos
diferentes:

- **Regressão** (AqDados): tolera ruído de medição, resume tudo numa reta + offset, reporta R.
  Bom quando a relação é fisicamente linear e os pontos têm dispersão.
- **Interpolação por segmento** (Table scale do DAQmx, nosso atual): passa por todos os pontos,
  linear entre eles. Bom para curvas não-lineares amostradas.

Decisão a tomar quando formos mexer na calibração: suportar **os dois modos** (espelhando o
AqDados) e expor a **correlação** quando for regressão. Não resolver agora; registrado como
pendência no [ADR-006](adr/006-calibracao-por-pontos.md).

### 1.4 Configuração avançada do módulo (ponte/condicionamento)

Tela "Configuração das Entradas Analógicas do Módulo" com colunas/controles de condicionamento de
sinal — vocabulário que o dono usa e que mapeia em conceitos de DAQ:

- **Ganho** (por canal): `x1, x2, x5, x10, x20, x50, x100, x200, x500, x1000, USER`.
- **Balanço** — balanceamento de ponte (bridge nulling no hardware).
- **Repouso** (e **Repouso Eng**) — valor de repouso/zero do canal.
- **Shunt Cal** (e **Shunt Eng**) — **calibração por resistor shunt**: técnica padrão de verificação
  de ponte (insere um shunt conhecido e confere a leitura esperada). Não temos isso; é candidato
  futuro para o strain.
- **Filtro Passa Banda** (ex.: `5 Hz`) — filtro por canal (anti-aliasing / banda de interesse).
- **Chaves de Ganho** (`JSH… Sw7 OFF Sw8 OFF`) — chaves físicas de ganho do hardware Lynx.
- **Junta Fria** — compensação de junta fria (para termopar).

Nem tudo se aplica ao nosso hardware NI, mas é o **léxico do dono** — útil para nomear telas e
opções de forma que ele reconheça.

---

## 2. AqDAnalysis — análise e relatório

Software de análise (versão vista: **7.0**). Abre o `.LDT` do AqDADos e processa os sinais.
**Esta é a ferramenta que decidimos NÃO reescrever** — em vez disso, exportamos para ela
(ver §4 e [ADR-011](adr/011-estrategia-de-exportacao.md)).

### 2.1 Visualização de série temporal + cursores

- Gráficos de série temporal empilhados (um por canal/eixo), eixo X em **tempo** (`mm:ss`).
- Painel de **cursores duplos** de medição: `Y1, T1, Y2, T2, ΔY, ΔT, ΔY/ΔT` e **`1/ΔT` em Hz** —
  ou seja, mede **frequência** direto entre dois pontos do gráfico. Referência para o nosso futuro
  data viewer.
- Abas de organização: **Info, Sinais, Eventos, Sheet**.
- Conceito **"Consulta"** = uma janela de análise/visualização salva sobre os dados (uma "query").

### 2.2 Menu "Análise" — a suíte pesada

Funções de análise disponíveis (a maioria é o que **deixamos para o AqDAnalysis fazer**):

- **Auto Espectro** (FFT / espectro de potência) e **Espectro Cruzado**.
- **Função de Transferência**, **Cepstrum / Inversa do Cepstrum**.
- **Estatística por Trechos**.
- **Análise de Rainflow**, **Análise de Markov**, **Análise de Fadiga**, **Biblioteca de Fadiga**.
- **Análise de Conforto** (vibração x norma de conforto humano).

É uma suíte de engenharia de vibração/fadiga madura. **Reescrever isso seria um projeto inteiro** —
e competiria com algo que o dono já domina e gosta. Por isso a estratégia é interoperar, não clonar.

### 2.3 Menu "Ferramentas" — pré-processamento e I/O

- **Ajuste de Escala e Linearização** — re-escala depois da aquisição.
- **Filtragem** — filtros digitais.
- **Filtragem de Spikes** — **remoção de outliers** (confirma que outlier é etapa de
  **pós-processamento**, distinta do clamp da conversão — como já dizia o ADR-006).
- **União Série e Paralela / Concatenação de Séries Temporais** — juntar ensaios.
- **Seleção de Trechos por Estatística**.
- **Importa Arquivo Texto** — **importa TXT** (a porta de entrada para os nossos dados).
- **Exporta Propriedades de Canais**, **Edita Arquivo de Série Temporal**.

### 2.4 Relatório técnico (menu "Relatório")

Gera relatório com **metadata de rastreabilidade**: Instituição, Área (ex.: "Monitoramento de
Estruturas"), Documento de Referência, Título/Rodapé, **Data**, **Responsável**, Obra, Observação,
e opções de gráfico (grid, cotas, fonte). Confirma a importância de **carregar metadata do ensaio**
junto dos dados — algo que o nosso CSV/TXT e o futuro dashboard devem suportar.

---

## 3. FlexLogger — comparação (referência só técnica)

- Selo **"This software trial will expire in 37 days"**: confirma que é a peça **paga** e que o
  dono está num trial contra o relógio. Reforça a urgência do projeto.
- Organização em abas: **Channel Specification / Logging Specification / Test Specification /
  Screen**.
- **Logging em TDMS** com opção **"Export automatically to CSV file format when logging completes"**
  (data rate configurável) e **Test properties** (metadata do teste). Útil saber que o FlexLogger
  também produz CSV.
- Tipos de gráfico do dashboard: **Long History Graph**, **High Speed Graph**, **Frequency Graph
  (FFT)** e **XY Graph**. O **XY Graph** é o **carga × deformação** (um canal no X, outro no Y) —
  referência direta para o nosso futuro dashboard de ensaio estático.
- Paleta de widgets (Booleans: LED, botões, switches; Drawings) — referência de biblioteca de
  componentes para o dashboard, não prioridade.

---

## 4. Formato de arquivo — o caminho real de interoperabilidade

Confirmado pelo dono (mensagens de 23/06/2026):

- O AqDados grava em **`.LDT`** — formato **proprietário**; **só o AqDAnalysis abre**. Sem
  especificação pública → **não vamos gerar `.LDT`**.
- O AqDAnalysis **exporta TXT** e **importa TXT** ("Importa Arquivo Texto").

**Implicação (corrige a conclusão pessimista anterior).** A doc antiga
([referencia-flexlogger.md §5](referencia-flexlogger.md)) dizia que compatibilidade de arquivo era
"improvável" porque o AqDAnalysis "não importa CSV de terceiros". O detalhe que faltava: ele
**importa TXT**. Logo **há um caminho real**: o nosso software gera um **TXT no layout que o
"Importa Arquivo Texto" aceita**, e o dono faz toda a análise (FFT, fadiga, relatório) na
ferramenta que já domina.

**Atenção — extensão ≠ formato.** `.BIN` (Catman), `.MEA` (MGCPlus), `.LDT` (Lynx) são formatos
**binários estruturados**; renomear um CSV para `.BIN` **não funciona** (o leitor espera bytes numa
estrutura específica). O caminho é **converter o conteúdo** para o layout-alvo, não trocar a
extensão. TXT é texto aberto, por isso é viável.

**Incógnita a fechar na implementação:** o layout exato que o "Importa Arquivo Texto" do AqDAnalysis
espera — separador (tab/`;`/espaço), cabeçalho, linha de taxa de amostragem, e **decimal com vírgula**
(as telas mostram `1,2241`, padrão BR/Lynx). Fechar testando no Windows ou na documentação da Lynx.
Ver [ADR-011](adr/011-estrategia-de-exportacao.md).

---

## 5. Resumo do que herdamos do Lynx

| Área | O que herdar | Onde entra |
| ---- | ------------ | ---------- |
| Vocabulário | Sinal, Aferição, Balanço, Repouso, Shunt Cal, Consulta, Sinais/Eventos | UI, CONTEXT.md |
| Unidades | µm/m (strain), mm/s² (aceleração), °C (PT100) | `canais.toml`, conversão |
| Calibração | dois modos: **Regressão Linear** e **Ganho e Ponto de Referência**; mostrar **correlação** | ADR-006 (a refinar) |
| Tipos de sensor | PT100 e outras curvas prontas, além de linear | conversão futura |
| Aquisição | tabela de canais (nome, unidade, tipo, faixa, limites) | config + futura UI |
| Análise | **não reescrever**; exportar TXT pro AqDAnalysis | ADR-011 |
| Dados | metadata de rastreabilidade (instituição, obra, responsável, data) | CSV/TXT + dashboard |
| Dashboard | série temporal + cursores (ΔY, ΔT, 1/ΔT=Hz), **XY graph** (carga×deformação) | Fase 3 |
