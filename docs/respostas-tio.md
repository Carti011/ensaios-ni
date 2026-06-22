# Respostas do dono do hardware — ensaios-ni

Registro do que o dono do equipamento (tio do Weslley) informou sobre o setup físico dos ensaios. É a **fonte de verdade para o futuro `config/canais.toml`** e para a configuração das tasks de aquisição. Atualizar a cada rodada de perguntas.

> As duas informações que **bloqueiam a Fase 3 (conversão)** estão marcadas com 🔴. Sem elas o software lê os volts mas o número não vira grandeza física.

---

## Placar

| Frente | O que precisamos | Status |
| ------ | ---------------- | ------ |
| Divisão dos módulos | qual é strain, quais são tensão | ✅ respondido |
| Excitação no 9205 | os módulos de tensão fornecem excitação? | ✅ não fornecem |
| Rede | topologia e tipo de IP | 🟡 falta o número do IP |
| Amostragem (vibração) | taxa em Hz | ✅ 1024 Hz |
| Amostragem (carga × deformação) | taxa dos ensaios lentos | ❌ pendente |
| **9235 — gage factor** | fator do extensômetro (vem da caixa) | 🔴 **bloqueia conversão** |
| 9235 — ponte/resistência | 120 Ω em quarter-bridge | ✅ confirmado pela etiqueta física (22/06/2026) |
| 9235 — canais | quantos canais e o que cada um mede; comprimento dos cabos | ❌ pendente |
| **9205 — conversão** | fórmula volts→unidade por canal | 🔴 **bloqueia conversão** |
| 9205 — canais | que sensor em cada canal; diferencial ou single-ended | ❌ pendente |
| Ensaio | duração típica e o que é um "resultado" a salvar | ❌ pendente |

---

## Rodada 1 — 21/06/2026 (4 áudios)

### Confirmado

- **Divisão dos módulos:** o **9235** é usado **só para strain gauge**; os **dois 9205** são usados **só para leitura de tensão**.
- **Excitação:** os 9205 **não fornecem excitação nem alimentam os sensores** — logo os transdutores de tensão já chegam com sinal "pronto" (saída condicionada ou alimentação externa). *(confirmado por voz pelo Weslley após reescutar o áudio 1.)*
- **Rede:** chassi ligado **direto no PC** (sem switch), com **IP fixo** configurado pelo dono.
- **Amostragem (vibração):** **1024 Hz**.

### Transcrição dos áudios

Transcrito local com `mlx-whisper` (modelo `large-v3-turbo`). Áudios curtos; correções óbvias da transcrição marcadas entre colchetes.

- **Áudio 1:** "Tenho a placa **9235** [«29235»], ela é só pra **strain gauge** [«stringage»]. As outras são só tensão, só leem tensão — não têm **voltagem** [«vontade»] nelas, não têm excitação." — *confirmado pelo Weslley.*
- **Áudio 2:** "Estou conectando ela no IP fixo que coloquei nela, do chassi direto no PC, direto no **notebook** [«notch»]."
- **Áudio 3:** "O tipo de amostragem do ensaio: pra vibração a gente usa 1024 Hz."
- **Áudio 4:** "Amostragem de 1024 Hz." *(confirma o áudio 3.)*

### Consequências para o software

- As tasks de tensão (9205) são **leitura crua de volts, sem configurar excitação** — alinhado com a [ADR-001](adr/001-arquitetura-porta-adaptador.md) e o [contexto-hardware](contexto-hardware.md).
- A "armadilha do strain" (9235 com defaults errados da API) **continua aberta**: sem o gage factor e a confirmação de 120 Ω / quarter-bridge, não dá pra configurar a task de strain corretamente.
- 1024 Hz vale para **vibração**; falta a taxa dos ensaios de carga × deformação (provavelmente bem menor).

---

## Pendências

### 🔴 Bloqueiam a conversão (Fase 3)

1. **Gage factor** dos extensômetros + confirmação de **120 Ω em quarter-bridge** (9235).
2. **Fórmula volts→unidade** de cada canal de tensão (9205) — ou a folha/planilha de calibração de cada sensor.

### Demais

- 9235: quantos canais, o que cada um mede, comprimento dos cabos.
- 9205: que sensor em cada canal; ligação **diferencial** ou **single-ended**.
- Com qual sensor a **vibração (1024 Hz)** é medida — strain (9235) ou algo no 9205.
- Taxa de amostragem dos ensaios de **carga × deformação**.
- Duração típica de um ensaio e o que é um "resultado" a exibir/exportar.
- Número do **IP fixo** do chassi *(quando vier, fica só no cofre privado — não versionar, repo pode ser público).*

---

## Perguntas enviadas — Rodada 2 (21/06/2026)

Reformuladas na linguagem do dono (engenharia/instrumentação), as duas críticas no topo:

1. **9235 (strain gauge):** qual o **gage factor** dos extensômetros (número da caixa, tipo 2,0 / 2,1)? São de **120 Ω em 1/4 de ponte**?
2. **9205 (tensão):** para cada sensor, **quando ele lê X volts equivale a quanto** na unidade real (ex.: 10 V = tantos kgf)? Ou a folha/planilha de calibração de cada um.
3. **9235:** quantos canais e o que cada um mede? Cabos longos?
4. **9205:** o que há em cada canal (célula de carga, deslocamento, pressão…)? Ligação **diferencial** ou **single-ended**?
5. Os **1024 Hz** de vibração são medidos com qual sensor? E os ensaios de **carga × deformação**, qual taxa?
6. **Duração** de um ensaio típico? O que precisa **ver/salvar** no fim (gráfico carga × deformação, valor máximo, planilha)?
7. Número do **IP fixo** do chassi.

---

## Para o dono confirmar

Lista em linguagem do dono — marcar o que está certo ou corrigir:

- [ ] O módulo **9235** é usado **só para strain gauge** (extensometria).
- [ ] Os **dois 9205** são usados **só para ler tensão**; eles **não alimentam nem excitam** os sensores (os sensores de tensão são alimentados/condicionados por fora).
- [ ] O chassi liga **direto no computador** (sem switch), com **IP fixo**.
- [ ] A amostragem de **1024 Hz** é a usada nos ensaios de **vibração**.
