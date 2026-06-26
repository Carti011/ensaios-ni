# Runbook — validação no Windows (NI-MAX simulado)

Passo a passo para **validar a aquisição** depois que o ambiente já está montado
([guia-windows.md](guia-windows.md)). Fecha a parte da Fase 2 que não dá para fazer no Mac:
ver o `daqmx` lendo **tensão (9205)** e **strain (9235)**, no modo **finito** e **contínuo**,
contra o NI-MAX.

> **O que dá para validar no simulado vs no hardware.** Os dispositivos **simulados** do NI-MAX
> geram um sinal sintético (senoide/ruído) — então **não** dá para "bater o número físico" neles.
> No simulado o critério é: **monta a task e lê sem erro**, com o **timing** e os **parâmetros do
> strain corretos**, e o **contínuo flui e encerra limpo**. A validação do **número físico** (bater
> com o test panel sobre um sinal conhecido) é no **hardware do tio** (Fase 5), com este mesmo runbook.

---

## Pré-requisitos

1. Ambiente instalado pelo [guia-windows.md](guia-windows.md) (`pip install -e .[hardware]`, `pytest` verde).
2. No **NI-MAX**, dispositivos **simulados** criados: chassi **cDAQ-9184** + **2× NI 9205** + **1× NI 9235**.
3. Anote os **nomes reais** dos canais como aparecem no NI-MAX (ex.: `cDAQ9184-1820306Mod1/ai0`,
   `...Mod3/ai0`). Eles vão no `canais.toml`.

## Passo 1 — Config de validação

Copie `config/canais.exemplo.toml` para `config/canais.toml` e troque os nomes pelos do NI-MAX,
mantendo **um canal de tensão e um de strain**. Exemplo:

```toml
[canais."cDAQ9184-1820306Mod1/ai0"]
tipo = "tensao"
unidade = "kgf"
ganho = 100.0
offset = 0.0

[canais."cDAQ9184-1820306Mod3/ai0"]
tipo = "strain"
unidade = "µε"
ganho = 1000000.0
offset = 0.0
```

## Passo 2 — Leitura finita (tensão + strain)

```text
python -m ensaios_ni --fonte daqmx --config config/canais.toml --taxa 1024 --amostras 1024 --saida validacao-finita.csv
```

**Aprovação:**
- [ ] Rodou **sem erro** e gravou o CSV.
- [ ] O CSV tem a coluna de tensão **e** a de **microstrain (µε)**, com `tempo_s`.
- [ ] No NI-MAX, abrir o **test panel** do 9235 e confirmar que o canal de strain responde (no
      simulado, que há sinal; no hardware, que o número bate com uma carga conhecida).

## Passo 3 — Aquisição contínua

```text
python -m ensaios_ni --continuo --fonte daqmx --config config/canais.toml --taxa 1024 --bloco 256 --duracao-s 10 --saida validacao-continua.csv
```

**Aprovação:**
- [ ] Rodou ~10 s e **encerrou sozinho** (parada por duração), gravando o CSV.
- [ ] O `tempo_s` é **contínuo e crescente** (sem reiniciar a cada bloco) e cobre ~10 s.
- [ ] Repetir sem `--duracao-s` e encerrar com **Ctrl-C**: tem que **parar limpo** e o CSV ficar
      íntegro (cabeçalho + linhas até o momento da interrupção).

## Passo 4 — Conferência da armadilha do strain

No test panel do 9235 (ou nas propriedades da task), confirmar que a leitura usa **quarter-bridge,
120 Ω, 2,0 V** — **nunca** full-bridge 350 Ω / 2,5 V. O teste-guarda automatizado já trava isso no
código; este passo confirma no driver real. Ver [contexto-hardware.md §4](contexto-hardware.md) e
[ADR-009](adr/009-leitura-de-strain-9235.md).

---

## Resultado

| Validação | Comando | Critério |
| --------- | ------- | -------- |
| Finita tensão+strain | `--fonte daqmx ... --amostras` | grava CSV com tensão e µε, sem erro |
| Contínua por duração | `--continuo ... --duracao-s 10` | encerra sozinho, tempo contínuo |
| Contínua por Ctrl-C | `--continuo ...` (sem duração) | encerra limpo, CSV íntegro |
| Armadilha strain | test panel do 9235 | quarter-bridge 120 Ω / 2,0 V |

Com os quatro itens marcados no **simulado**, a Fase 2 está validada no Windows. O número físico
fica para a Fase 5, no hardware do tio, com este mesmo runbook.
