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

```
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

## Fontes

- [NI-DAQmx Custom Scales and Usage Explained](https://www.ni.com/en/support/documentation/supplemental/18/ni-daqmx-custom-scales-and-usage-explained.html)
- [Custom Scales — NI-DAQmx Product Documentation](https://www.ni.com/documentation/en/ni-daqmx/latest/mxcncpts/customscales/)
- [Scaling Electrical Values to Physical Values — FlexLogger Manual](https://www.ni.com/documentation/en/flexlogger/latest/manual/scaling-electrical-values/)
- [Configuring Scaling for FlexLogger Load Cell Channel](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000001DbGQSA0)
- [Calibration or Zero. What are the differences? — NI Community](https://forums.ni.com/t5/FlexLogger/Calibration-or-Zero-What-are-the-differences/td-p/3886516)
- [nidaqmx.scale — nidaqmx Python docs](https://nidaqmx-python.readthedocs.io/en/latest/scale.html)
