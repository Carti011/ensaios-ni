# Referência — como o FlexLogger/NI-DAQmx resolve escala, zero e fora-de-faixa

Documento de referência (pesquisa de 23/06/2026). O objetivo do projeto é **substituir o
FlexLogger** (única peça paga da pilha NI) mantendo o **mesmo modelo mental** que o dono do
hardware já domina, com UX mais moderna. Para isso, espelhamos as decisões do FlexLogger —
que por baixo são as **Custom Scales do NI-DAQmx**. Ver [ADR-008](adr/008-paridade-funcional-flexlogger.md).

> Fonte de verdade do comportamento. Quando uma decisão de conversão/calibração precisar de
> referência, é aqui (e nas páginas da NI linkadas no fim). Não inventar comportamento próprio
> quando o FlexLogger já define um.

---

## 1. Escala (conversão volts → unidade) = Custom Scales do DAQmx

O FlexLogger não tem conversão própria: ele configura **Custom Scales** do NI-DAQmx. São quatro
tipos; dois cobrem todo o nosso caso:

| Tipo | Método | Uso no nosso projeto |
| ---- | ------ | -------------------- |
| **Linear** | `y = m·x + b` (`x` = pré-escalado/volts, `y` = escalado). Equação idêntica para entrada e saída. | Sensor **com** folha de dados / sensibilidade conhecida. É o [ADR-002](adr/002-conversao-linear-e-contrato-da-porta.md). **Caso particular de 2 pontos.** |
| **Table** | Pares `(pré-escalado, escalado)`. **Interpolação linear** entre os pontos da tabela. | Sensor **sem** fórmula fechada (a maioria, segundo o dono): aplica carga conhecida, lê a voltagem, monta a curva ponto a ponto. É a **calibração por pontos** do [ADR-006](adr/006-calibracao-por-pontos.md). |
| Map Ranges | Escala proporcional de uma faixa pré-escalada para uma faixa escalada. | Não usamos. |
| Polynomial | Polinômio de ordem `n`, com coeficientes forward (pré→escalado) e reverse. | Futuro, só se um sensor exigir curva não-linear suave. |

**Pré-escalado** = valor antes da escala (tipicamente volts). **Escalado** = valor final na
unidade de engenharia definida pelo usuário (kgf, mm, MPa, microstrain…).

### Célula de carga no FlexLogger (atalho linear por sensibilidade)

Quando há folha de dados, o FlexLogger calcula o slope a partir da sensibilidade em **mV/V**:

```text
slope = faixa_total_de_carga / sensibilidade
# ex.: célula 1000 N, 3 mV/V  →  slope = 1000 / 3 = 333 N/(mV/V)
```

É o caminho rápido **quando se tem a especificação**. Sem ela (caso recorrente do dono), cai na
escala por **tabela de pontos**.

## 2. Zero / tara — botão "Zero Channel"

O FlexLogger separa **duas** operações de anulação de offset, em camadas diferentes:

- **Calibration (bridge offset / nulling no driver):** captura a tensão de offset inerente ao
  sensor de ponte e anula no **nível do driver DAQ**. É o `initial_bridge_voltage` do strain.
- **Zero Channel (na aplicação):** lê o **próximo buffer** de amostras, tira a **média** e grava
  esse valor como o **offset (`b`)** da escala (`y = m·x + b`). É a **tara** clássica — "zerar a
  balança antes de pôr peso".

Para o nosso domínio, a **tara é o Zero Channel**: capturar N amostras de repouso, calcular a
média, subtrair do sinal. É operação **separada da calibração** (a escala/slope), e vive no
domínio (testável no Mac). Ver [ADR-006](adr/006-calibracao-por-pontos.md).

## 3. Fora da faixa de calibração — clip (clamp) na leitura

Comportamento do DAQmx para a escala por **tabela**:

> *"Read operations will **clip** samples that are outside the maximum and minimum scaled values
> found in the table."* (operações de escrita, ao contrário, geram erro.)

Ou seja: na **leitura** (nosso caso — aquisição), o valor fora do intervalo da tabela é
**saturado (clamp)** no extremo mais próximo. Adotamos o mesmo. Decisão fundamentada no
[ADR-006](adr/006-calibracao-por-pontos.md).

### Clamp ≠ remoção de outliers

São camadas distintas e **não conflitam**:

- **Clamp (conversão):** acontece na hora de transformar volts em unidade, durante a aquisição.
  Evita número absurdo por extrapolação. **Não descarta dado** — satura.
- **Remoção de outliers (análise):** etapa de **pós-processamento** (território do AqDAnalysis),
  roda depois do ensaio, sobre os dados já gravados. Identifica e remove/marca pontos impossíveis.
  É feature futura de análise, fora do escopo da conversão.

## 4. Pendências que dependem do dono (não do FlexLogger)

A pesquisa fechou o **comportamento**; faltam **números reais** do dono (vão pra rodada 3 em
[respostas-tio.md](respostas-tio.md)):

- Sensibilidades/faixas dos sensores (semente das tabelas de calibração).
- Confirmar que ele zera (tara) cada canal no início de todo ensaio.
- Formato de arquivo para abrir no AqDados/AqDAnalysis.

---

## 5. Estudo de mercado (23/06/2026) — respostas obtidas sem o tio

Pesquisa (Google + docs NI/Lynx + site da OFM) que respondeu boa parte da rodada 3 antes de
falar com o dono. Confiança indicada em cada item.

- **Acelerômetro = Dytran (EUA).** ✅ alta. O site da OFM cita "Acelerômetros Dytran (EUA)",
  triaxiais, alta sensibilidade, resolução sub-mg (usados na aferição da Ponte Rio–Niterói). O
  "de tram" do áudio é **Dytran**. Falta só o modelo/sensibilidade exatos.
- **Fiação do 9205 → diferencial.** ✅ alta (recomendação). Para instrumentação em campo com cabo
  longo, o padrão NI é medir **diferencial** com par trançado blindado (rejeição de ruído de modo
  comum); fonte flutuante exige resistores de bias. O 9205 oferece 16 canais diferenciais. A
  config real do dono ainda é dele, mas a recomendação é clara.
- **Taxa dos ensaios lentos (estáticos) → baixa.** ✅ média. Provas de carga estáticas usam
  ~**0,02 a 10 Hz** (1 Hz típico, ou uma leitura por estágio de carga); o dinâmico fica em
  50–256 Hz (o dono usa 1024 Hz na vibração). Falta o valor exato dele.
- **Fora da faixa → clamp.** ✅ alta (já fechado na §3). Outliers são pós-processamento (AqDAnalysis).
- **Célula de carga no 9205 → precisa de condicionador externo.** ✅ alta. Célula é ponte (mV/V,
  precisa excitação); o 9205 **não excita**. Liga via condicionador/amplificador com **saída em
  tensão** (±10 V centrada em 0), ou módulo de excitação dedicado. A OFM calibra células com
  rastreabilidade INMETRO/RBC (linearidade, histerese, sensibilidade) — então as células dela são
  bem caracterizadas. Falta confirmar **qual** condicionamento ele usa.
- **Formato de arquivo (AqDAnalysis) → proprietário na entrada, TXT na troca.** ⚠️ importante. O
  AqDAnalysis **importa formatos proprietários** (Lynx nativo, HBM Catman `.BIN`, MGCPlus `.MEA`,
  MTS RPC III) e **converte para TXT/ASCII**. Ele **não importa CSV de terceiros** nativamente.
  Implicação de design: **paridade direta de arquivo com o AqDAnalysis é improvável**; o caminho
  realista é gerar **CSV/TXT legível** (e, no futuro, nossa própria análise/FFT estilo AqDAnalysis,
  já que substituímos o FlexLogger, não o AqDAnalysis). Confirmar se ele consegue importar TXT lá.
- **Tara → prática padrão, ordem de segundos.** ✅ média. "Zero Channel" do FlexLogger usa o
  próximo buffer; AqDados tem balanceamento. Tempo de repouso típico = alguns segundos de média.
  Falta o tempo/nº de amostras exato dele.
- **Features centrais do FlexLogger (o que substituir):** dashboard ao vivo (arrastar-soltar),
  gráficos em tempo real, logging em disco sem programar, **workflow de configuração por tipo de
  sensor**, **metadata do teste para rastreabilidade**, data viewer integrado para revisar o
  ensaio, e (versão completa) triggers/eventos/estatística. É o conjunto que nosso software precisa
  cobrir aos poucos.

## Fontes

- [NI-DAQmx Custom Scales and Usage Explained](https://www.ni.com/en/support/documentation/supplemental/18/ni-daqmx-custom-scales-and-usage-explained.html)
- [Custom Scales — NI-DAQmx Product Documentation](https://www.ni.com/documentation/en/ni-daqmx/latest/mxcncpts/customscales/)
- [Scaling Electrical Values to Physical Values — FlexLogger Manual](https://www.ni.com/documentation/en/flexlogger/latest/manual/scaling-electrical-values/)
- [Configuring Scaling for FlexLogger Load Cell Channel](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000001DbGQSA0)
- [Calibration or Zero. What are the differences? — NI Community](https://forums.ni.com/t5/FlexLogger/Calibration-or-Zero-What-are-the-differences/td-p/3886516)
- [nidaqmx.scale — nidaqmx Python docs](https://nidaqmx-python.readthedocs.io/en/latest/scale.html)
- [Lynx AqDAnalysis (formatos: Lynx, HBM Catman .BIN, MGCPlus .MEA, MTS RPC III; export TXT)](https://www.lynxtec.com.br/sw_AqDAnalysis.htm)
- [NI 9205 Getting Started (diferencial/single-ended, fiação)](https://www.ni.com/docs/en-US/bundle/ni-9205-getting-started/page/overview.html)
- [What Is NI FlexLogger? (features: dashboard, logging, metadata, data viewer)](https://www.ni.com/en/shop/data-acquisition-and-control/flexlogger)
- Site institucional OFM Engenharia (`codigo/ofm-engenharia`): acelerômetros Dytran, LVDTs, strain gages, PT100, calibração de células com rastreabilidade INMETRO/RBC.
