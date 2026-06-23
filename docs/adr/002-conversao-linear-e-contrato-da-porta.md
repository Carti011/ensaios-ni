# ADR 002 — Conversão linear por canal e contrato da porta de aquisição

## Status

Aceito — **estendido por [ADR-006](006-calibracao-por-pontos.md)** (calibração por pontos + tara) e por [ADR-005](005-contrato-multicanal-da-porta.md) (contrato multi-canal). O `ganho·V + offset` deixa de ser o modelo único e passa a ser o caso particular de uma calibração de 2 pontos.

## Contexto

O [ADR-001](001-arquitetura-porta-adaptador.md) deixou explicitamente pendente **o que a porta `FonteDeAquisicao` retorna** (arrays brutos? com timestamp? por canal nomeado?). A Fase 1 implementa a fatia mínima de leitura + conversão rodando no Mac, e isso exige fechar esse contrato.

Há também uma decisão de domínio implícita que precisa virar explícita: **a conversão volts→unidade de engenharia é linear**. Os sensores reais ainda não foram levantados com o dono do hardware (gargalo da §6 de [contexto-hardware.md](../contexto-hardware.md)). O que se espera: célula de carga e transdutor de pressão (**lineares**), mas possivelmente também termopar (**não-linear**). Modelar tipos de sensor que ainda não conhecemos seria especulação.

## Decisão

- **A porta retorna volts brutos.** `ler_tensao(canal, amostras) -> list[float]` devolve tensão crua, sem timestamp e sem conversão. Converter **não** é responsabilidade da aquisição.
- **A conversão é linear por canal:** `valor = ganho * volts + offset`, parametrizada por `config/canais.toml` (nunca hardcode). Vive no domínio, não no adaptador.
- **A config é entrada externa e é validada no carregamento:** campos obrigatórios (`tipo`, `unidade`, `ganho`, `offset`) e tipos numéricos. Canal ausente levanta `CanalNaoConfigurado`; config malformada levanta `ConfiguracaoInvalida` apontando canal e campo.

## Consequências

**Melhora:**

- Cobre os sensores lineares (célula de carga, transdutor de pressão), que são a maioria esperada.
- Domínio 100% testável no Mac, sem `nidaqmx`.
- Erros de config falham cedo e claros, em vez de produzir número plausível e errado.

**Piora / pendente:**

- **Termopar e strain não são lineares.** Quando aparecerem, a conversão vira uma estratégia por tipo (ex.: campo `conversao = "linear" | "polinomial"` no canal, ou escala/tabela). Isso será um ADR-003 quando o dono confirmar os sensores. Até lá, o campo `tipo` é só metadado (será usado na Fase 2 para escolher a task DAQmx correta).
- **Timestamp / sample clock no retorno da porta** fica para a Fase 2 (aquisição contínua); pode virar ADR próprio se a decisão não for trivial.
