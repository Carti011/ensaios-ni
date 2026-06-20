# ADR 001 — Arquitetura porta/adaptador para isolar o NI-DAQmx

## Status

Aceito

## Contexto

A camada que conversa com o hardware (`nidaqmx` sobre o driver NI-DAQmx) **só existe em Windows e Linux x86** — não roda em macOS nem ARM. O desenvolvimento principal acontece num MacBook M4. O hardware físico está na casa do dono do equipamento, acessível só esporadicamente.

Se o código de aquisição importar `nidaqmx` diretamente nas regras de negócio (conversão volts→unidade, persistência, apresentação), nada disso pode ser importado nem testado no Mac. O TDD — obrigatório por padrão de trabalho — ficaria refém de um PC Windows, que nem sempre está disponível. O caminho de "dispositivo simulado do NI-MAX" não resolve: ele também exige Windows e é um teste de integração, não o loop unitário rápido do red-green-refactor.

## Decisão

Adotar **arquitetura hexagonal (porta/adaptador)** para a aquisição:

- Uma **porta** `FonteDeAquisicao` (interface) define o contrato — algo como `ler_tensao()` e `ler_strain()`. É a única coisa que o resto do sistema conhece.
- Dois **adaptadores** implementam a porta:
  - `daqmx.py` — real, sobre o `nidaqmx`. **Único arquivo do projeto autorizado a importar `nidaqmx`**, e o import é **lazy** (dentro das funções). Roda só em Windows.
  - `fake.py` — sintético, Python puro, devolve dados plausíveis. Roda em qualquer lugar, inclusive Mac.
- **Domínio, conversão, persistência e apresentação dependem só da porta**, nunca de um adaptador concreto. A escolha do adaptador acontece na borda (composição/injeção), por ambiente.
- `nidaqmx` é **dependência opcional** (extra `[hardware]` no `pyproject.toml`). O pacote importa e os testes de domínio rodam no Mac sem ela instalada.

## Consequências

**Melhora:**

- TDD real (red-green-refactor) no Mac para ~90% do código — conversão, persistência, regras de ensaio, lógica do dashboard.
- O acoplamento ao Windows/DAQmx fica confinado a um único arquivo, fácil de auditar.
- O fake permite desenvolver e demonstrar o fluxo ponta a ponta sem nenhum hardware nem NI-MAX.

**Piora / custo:**

- Uma camada de indireção a mais (a porta). Justificada pela restrição de plataforma; não é abstração gratuita.
- O **adaptador real continua só testável no Windows**. A porta não elimina isso — só isola. A validação do `daqmx.py` é feita contra dispositivos simulados (Windows) e, no fim, contra o test panel do NI-MAX no hardware real.
- Exige disciplina: qualquer `import nidaqmx` fora do `daqmx.py` quebra a premissa. Vale uma checagem automatizada (teste/lint) que falha se `nidaqmx` for importado em outro lugar.

**Pendente:**

- Definir a assinatura exata da porta quando a Fase 2 começar (o que `ler_tensao`/`ler_strain` retornam: arrays brutos? já com timestamp? por canal nomeado?). Pode virar ADR-002 se a decisão for não-trivial.
