# ADR 020 — Parâmetros de strain por canal na config

## Status

Aceito (30/06/2026). Refina o [ADR-009](009-leitura-de-strain-9235.md), que registrara o gage
factor como "por-task (uma `ConfigStrain` por adaptador), não por-canal — refina quando o dono
mandar os valores reais". Esse refinamento agora foi feito.

## Contexto

Na primeira validação no hardware real do tio (29/06/2026), o gage factor confirmado do
extensômetro em uso é **2,14**. O código tinha o gage factor fixo no `ConfigStrain` (default 2,15),
configurável só por construtor — e a CLI instanciava `AdaptadorDaqmx()` sem passá-lo, então as
leituras saíam com **2,15 (errado e silencioso)**. Ajustar exigia um script manual. Além disso, o
gage factor **varia por extensômetro** (2,14–2,16 por lote) e um ensaio pode ter vários gages com
factors diferentes — uma config única por adaptador não cobre o caso real do tio.

## Decisão

- **Os parâmetros físicos do extensômetro passam a viver na config de cada canal**, no domínio:
  novo value object `ParametrosStrain` (`dominio/canais.py`) e campo opcional `Canal.strain`,
  lidos do `canais.toml` por canal de strain.
- **Configuráveis no TOML** (por canal): `gage_factor`, `poisson`, `resistencia` (nominal do gage),
  `resistencia_cabo` (lead wire, 3 fios). Omitidos caem nos **defaults seguros do 9235**.
- **Excitação (2,0 V) e ponte (quarter-bridge) ficam FIXAS** — são do hardware do 9235 e **não**
  vêm da config: torná-las editáveis reabriria a armadilha do strain (número errado e silencioso).
  A regra 5 do `CLAUDE.md` segue valendo.
- **`ConfigStrain` (no adaptador) é removido**; o `AdaptadorDaqmx` recebe os `Canais` e usa o
  `ParametrosStrain` de cada canal ao montar a task (default seguro quando ausente). A CLI passou a
  injetar os canais no adaptador.

## Consequências

**Melhora:**

- O gage factor real (2,14) sai do `canais.toml`, por canal — fim do script manual e do 2,15 errado.
- Cobre o caso do tio com vários extensômetros de factors distintos no mesmo ensaio.
- A armadilha do strain continua travada por teste; excitação/ponte não-editáveis fecham um vetor de erro.
- `ParametrosStrain` vive no domínio (puro, sem `nidaqmx`) — testável no Mac; o adaptador só consome.

**Piora / pendente:**

- A validação do **número físico** (comparar a variação carregado−repouso com o NI-MAX no mesmo
  canal/unidade) continua pendente — ver [guia-teste-hardware.md](../guia-teste-hardware.md) e o
  handoff da Fase 5.
