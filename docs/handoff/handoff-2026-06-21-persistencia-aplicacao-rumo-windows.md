# Handoff: persistência CSV, camada de aplicação e demonstração executável (rumo ao Windows)

**Data:** 2026-06-21
**Status:** em andamento — espinha de software completa e testada no Mac; próximo passo é configuração inicial no Windows e, na volta, a Fase 2 (adaptador `daqmx.py`)

## 1. Objetivo

Substituir LabVIEW/FlexLogger (pagos) por software próprio em Python sobre o driver
gratuito NI-DAQmx, para o hardware do tio do Weslley (OFM Engenharia — instrumentação e
análise experimental de estruturas: chassi cDAQ-9184 + 2× NI 9205 de tensão + 1× NI 9235
de strain). Esta sessão completou a **espinha de software no Mac**: gravar um ensaio em
CSV, orquestrar leitura→conversão→gravação num caso de uso, e expor um ponto de entrada
que roda o fluxo inteiro com o adaptador fake. Tudo roda **100% no Mac M4, sem hardware e
sem `nidaqmx`**, via TDD.

## 2. Contexto essencial

- **Domínio do cliente (descoberto nesta sessão pelo site `~/cofre/codigo/ofm-engenharia/`):**
  o tio faz **provas de carga** (estático → gráfico carga×deformação) e **análise de
  vibração** (dinâmico → frequências naturais em Hz via FFT). Sensores: strain gages,
  células de carga, LVDTs, **acelerômetros**. Consequência técnica forte: **o resultado de
  um ensaio é uma série temporal amostrada a taxa fixa**, não um número solto. Os sensores
  entram como tensão no 9205 (acelerômetro, célula, LVDT) ou strain no 9235.
- **Restrição que define tudo:** NI-DAQmx só roda em Windows/Linux x86. O Mac só
  desenvolve e testa domínio/fake. O pacote precisa importar e os testes do domínio
  precisam rodar sem `nidaqmx`.
- **Arquitetura (ADR-001):** porta/adaptador. Tudo depende da interface `FonteDeAquisicao`.
  Dois adaptadores: `daqmx` (real, Windows, único que importa `nidaqmx`, lazy — **ainda não
  existe**) e `fake` (sintético, Mac).
- **Decisões acumuladas:** ADR-002 (porta retorna volts brutos; conversão linear por canal
  `ganho·V + offset` em config); **ADR-003 (novo)** — persistência CSV; **ADR-004 (novo)** —
  camada de aplicação e ponto de entrada.
- **Divisão de trabalho confirmada pelo Weslley nesta sessão:** **todo desenvolvimento é no
  Mac.** Windows (dele e do tio) é só **configuração/execução inicial** — nunca programar
  lá. Por isso o `CLAUDE.md` foi enxugado (removidas regras de processo de dev e o runbook
  "para agente"); a instalação no Windows vive em `docs/guia-windows.md`, para humano.
- **Stack:** Python 3.12 (via `uv`), `pytest`. `nidaqmx` é extra opcional `[hardware]`, não
  instalado no Mac. `package = false` no `uv` (Mac não instala o próprio pacote).

## 3. O que já foi feito (nesta sessão)

Cronológico:

- **Recapitulação completa** do projeto para o Weslley (ele tinha perdido o fio da Fase 1).
- **Persistência CSV** (`persistencia/csv_ensaio.py`), via TDD red-green, 5 testes:
  - grava 1 canal com coluna `tempo_s` derivada da taxa (`índice / taxa_hz`);
  - múltiplos canais alinhados pelo tempo (layout "wide");
  - unidade de engenharia no cabeçalho (`Mod1/ai0 (kgf)`);
  - recusa canais com contagens diferentes de amostras (`ValueError` claro);
  - recusa `taxa_hz <= 0`.
- **Camada de aplicação** (`aplicacao/ensaio.py`): caso de uso `executar_ensaio` que costura
  porta (aquisição) + domínio (conversão) + persistência, sem acoplar as camadas. 1 teste.
- **Ponto de entrada** (`__main__.py` + `aplicacao/demo.py`): `python -m ensaios_ni` roda um
  ensaio ponta a ponta com o fake e um sinal sintético senoidal (simula vibração), gera CSV.
  1 teste (smoke: cabeçalho + nº de linhas). **Rodado de verdade** e validado.
- **ADR-003** (persistência CSV) e **ADR-004** (camada de aplicação e ponto de entrada).
- **`docs/guia-windows.md`:** guia humano passo a passo de instalação no Windows, com trilha
  para quem tem Claude Code e para quem não tem (o PC do tio).
- **`CLAUDE.md` enxugado** + **README** (demonstração executável, nota config-driven) +
  **CHANGELOG**.
- **3 commits** na `develop` (feat persistencia / feat aplicacao / docs). Working tree limpo.

Decisões de design tomadas (registradas nos ADRs):

- Persistência recebe **valores já convertidos** (domínio converte, persistência só grava).
- Layout **wide** (abre no Excel, é o que FFT espera). `tempo_s` derivado da taxa.
- Nova camada `aplicacao/` (o "service") como única que conhece as três pontas.
- Sem value object `Medida` ainda (YAGNI, mantém a linha do ADR-002).

## 4. Estado atual

- **22 testes verdes** (`uv run pytest`), rodando no Mac sem `nidaqmx`. Antes eram 15.
- O teste-guarda de arquitetura (`tests/arquitetura/test_regra_nidaqmx.py`) continua verde:
  nenhum arquivo novo importa `nidaqmx`.
- O programa **roda ponta a ponta no Mac**: `PYTHONPATH=src uv run python -m ensaios_ni`
  gera `ensaio-demo.csv` (ignorado pelo git via `*.csv`) com `tempo_s` + 2 canais
  convertidos (kgf, bar) em senoide.
- Estrutura de código existente:
  - `src/ensaios_ni/dominio/` → `canais.py`, `conversao.py`, `erros.py`.
  - `src/ensaios_ni/aquisicao/` → `porta.py`, `fake.py`. (**não existe `daqmx.py`**)
  - `src/ensaios_ni/persistencia/` → `csv_ensaio.py`.
  - `src/ensaios_ni/aplicacao/` → `ensaio.py`, `demo.py`.
  - `src/ensaios_ni/__main__.py`.
- Branch `develop`, working tree limpo, 3 commits novos. **Nenhum push feito ainda** (o
  remote é `github.com/Carti011/ensaios-ni`; o Weslley precisa puxar/clonar no Windows, o
  que exige push — ver §5).

## 5. Bloqueios e dependências

- **Push pendente de decisão:** para o Weslley clonar/puxar no Windows, os 3 commits
  precisam ir para o GitHub. Push não é feito autonomamente — aguarda o "pode dar push".
- **Fase 2 exige Windows** com NI-DAQmx + dispositivos simulados no NI-MAX. O `daqmx.py`
  será **escrito no Mac** (com base na API pinada em `docs/contexto-hardware.md §4`) e
  **rodado/validado no Windows** contra o test panel do NI-MAX.
- **Gargalo real (não-código):** os itens da §6 de `docs/contexto-hardware.md` — que sensor
  em cada canal, **fórmula volts→unidade por canal**, gage factor do extensômetro,
  quarter-bridge 120 Ω, lead wire resistance, taxa/duração do ensaio, o que é um "resultado".
  O tio ainda não respondeu; espera-se que ele responda com perguntas — o Weslley traz as
  respostas/dúvidas e o agente traduz.

## 6. Próximos passos

**Imediato (o Weslley vai fazer agora):**

1. **(Decisão)** Autorizar o push da `develop` para o GitHub.
2. **(Windows, sem programar)** Seguir `docs/guia-windows.md`: instalar Python 3.12, driver
   NI-DAQmx + NI-MAX, `pip install -e .[hardware]`, rodar `pytest` (deve dar 22 passed),
   criar dispositivos simulados no NI-MAX, listar dispositivos. Pode pedir ao Claude Code do
   Windows: "leia o projeto inteiro e faça as configurações iniciais".

**Quando voltar ao Mac (Fase 2 — desenvolvimento):**

3. **Escrever `aquisicao/daqmx.py`** (o adaptador real), implementando a porta
   `FonteDeAquisicao`. Regras: `import nidaqmx` **lazy** (dentro das funções); task de tensão
   (2× 9205, `add_ai_voltage_chan`); task de strain (9235 com `QUARTER_BRIDGE_I`, 120 Ω,
   2,0 V — **nunca os defaults da API**, ver `contexto-hardware.md §4`). O teste-guarda
   permite `nidaqmx` só neste arquivo.
4. **Ponto de entrada de produção:** evoluir além da demo — carregar `config/canais.toml`,
   escolher o adaptador (fake vs daqmx), receber taxa/duração por CLI. Ver "pendente" do
   ADR-004.
5. **Validar no Windows** (rodar, não programar): comparar a leitura do `daqmx` com o test
   panel do NI-MAX no mesmo canal. É o critério objetivo de "funcionou".
6. **(Quando o tio responder)** ADR-005 para conversão não-linear (strain/termopar) e
   preencher `config/canais.toml` com nomes reais (do NI-MAX) e coeficientes reais.
7. **(Mais à frente)** Análise: FFT para frequência natural → ADR de escolha de biblioteca
   (numpy/scipy). A matemática não depende do tio; só os números reais dependem.

## 7. Artefatos relevantes

**Comandos:**

```bash
uv run pytest                                  # suíte (deve dar 22 passed)
PYTHONPATH=src uv run python -m ensaios_ni      # demo ponta a ponta no Mac (gera ensaio-demo.csv)
```

(No Windows, após `pip install -e .[hardware]`, a demo roda direto: `python -m ensaios_ni`.)

**Caso de uso (a costura)** — `src/ensaios_ni/aplicacao/ensaio.py`:

```python
def executar_ensaio(fonte, canais, amostras, taxa_hz, caminho):
    valores_por_canal, unidades = {}, {}
    for nome in canais:
        canal = canais[nome]
        volts = fonte.ler_tensao(nome, amostras)
        valores_por_canal[nome] = [converter(v, canal) for v in volts]
        unidades[nome] = canal.unidade
    gravar_ensaio(caminho, valores_por_canal, taxa_hz, unidades)
```

> Na Fase 2, `fonte` passa de `AquisicaoFake` para `AdaptadorDaqmx` — o caso de uso não muda.

**Persistência (assinatura)** — `src/ensaios_ni/persistencia/csv_ensaio.py`:

```python
def gravar_ensaio(caminho, amostras_por_canal, taxa_hz, unidades=None) -> None
# CSV "wide": tempo_s,<canal> (<unidade>) ; tempo_s = índice / taxa_hz
```

**Decisões:** `docs/adr/001`..`004`. **Hardware + API pinada:** `docs/contexto-hardware.md`.
**Glossário:** `CONTEXT.md`. **Instalação Windows (humano):** `docs/guia-windows.md`.

## 8. Como iniciar a próxima sessão

**Se for o Claude Code do Windows (só configuração inicial, não programar):**

1. Ler `docs/guia-windows.md` e o `README.md`.
2. Executar os passos de instalação: conferir Python, `pip install -e .[hardware]`, `pytest`
   (esperar 22 passed), confirmar driver NI-DAQmx/NI-MAX, criar dispositivos simulados,
   listar dispositivos (snippet em `docs/contexto-hardware.md §4`).
3. **Não** escrever código de produção. Se algo exigir desenvolvimento, anotar e devolver ao
   Weslley — o desenvolvimento volta a ser no Mac.

**Se for o próximo Claude Code no Mac (continuar o desenvolvimento):**

1. Abrir este handoff e o `CLAUDE.md`.
2. Rodar `uv run pytest` → **22 passed**. Se não der, o ambiente quebrou; recriar com
   `uv venv --python 3.12`.
3. Confirmar com o Weslley o foco: (a) se ele já validou o ambiente no Windows e quer a
   **Fase 2** → começar o `aquisicao/daqmx.py` via TDD, usando a API pinada em
   `contexto-hardware.md §4` e sem nunca usar os defaults de strain; (b) se o tio respondeu →
   atualizar `config/canais.exemplo.toml`/`canais.toml` e considerar ADR-005 (não-linear).
4. Manter vivos: o teste-guarda de arquitetura verde a cada commit; commits separados por
   camada; nada de commit/push autônomo; português em tudo.
