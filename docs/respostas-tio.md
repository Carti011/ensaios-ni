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
| Amostragem (carga × deformação) | taxa dos ensaios lentos | 🟡 não dito explicitamente (presumir baixa) |
| 9235 — gage factor | fator do extensômetro | ✅ **2,14–2,16, varia por lote** (configurável) |
| 9235 — ponte/resistência | 120 Ω em quarter-bridge | ✅ etiqueta + voz; cabo longo = **3 fios, 22 AWG** |
| 9235 — canais | quantos e o que medem | 🟡 varia por obra; não há número fixo |
| 9205 — conversão | volts→unidade por canal | ✅ **calibração por pontos + tara** (ver ADR-006) |
| 9205 — canais | que sensor em cada canal | ✅ LVDT, acelerômetro (alim. externa); célula de carga em dúvida |
| 9205 — fiação | diferencial ou single-ended | ❌ ainda não dito |
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

## Rodada 3 — perguntas reservadas (a enviar)

1. **Célula de carga:** a sua é de **saída em tensão** (condicionada/amplificada, ex. 0–10 V) ou de **ponte crua** (mV/V)? É o que define se liga no 9205 (que não excita).
2. **Sensibilidade/faixa dos sensores** (para semear a calibração): acelerômetro (**mV/g**, faixa ±2G), LVDT (faixa em **mm** e **V/mm**), pressão (faixa **MPa** e **V/MPa**), célula (**kgf** e V).
3. **Acelerômetro:** marca/modelo (no áudio soou "de tram") e sensibilidade exata.
4. **Fiação no 9205:** **diferencial** ou **single-ended**?
5. **Taxa dos ensaios lentos** (carga × deformação) — é bem menor que 1024 Hz? Quanto?
6. **Formato de arquivo:** o AqDados/AqDAnalysis importa **CSV**? Que layout/extensão você precisa para abrir os dados lá?
7. **Tara:** confirma que você **zera (null) cada canal no início** de todo ensaio?

---

## Rodada 1 — 21/06/2026 (histórico)

Confirmado: 9235 só strain; 2× 9205 só tensão (sem excitação); chassi direto no PC com IP fixo; vibração a 1024 Hz. Transcrições e detalhes preservados no histórico do git (commit `db48757`+).
