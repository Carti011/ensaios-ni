# ADR 023 — Configuração de canais na UI (biblioteca de perfis + discovery)

## Status

**Aceito** (02/07/2026). Detalha e promove a [tarefas-futuras.md §4](../tarefas-futuras.md)
("Interface gráfica para configurar os canais"). As decisões de produto abertas no rascunho foram
resolvidas pelo Weslley (ver "Decisões de produto (resolvidas)"). A implementação é **fatiada**: a
**Parte A** (perfis + editor, testável no Mac) é a próxima frente de desenvolvimento; a **Parte B
(discovery)** espera acesso ao Windows e o primeiro feedback do tio, conforme o
[ADR-019](019-foco-em-validacao-fisica-e-adocao.md). Entra na **Fase 6** (adoção) do
[roadmap.md](../roadmap.md).

## Contexto

Hoje a configuração dos canais vive num `canais.toml` que **alguém edita à mão** — o Weslley
preenche antes de enviar o `.exe`, ou o tio abriria o arquivo. A tela inicial
([ADR-015](015-ux-e-fluxo-do-dashboard.md), estado "Sem config") só oferece **"Abrir configuração…"**
(escolher um `.toml`). Para um usuário leigo em TI, **lidar com arquivo de configuração é atrito
real** — o próprio tio observou que no FlexLogger "já reconhecia tudo", sem esse passo. O FlexLogger/
AqDados fazem **discovery automático** dos dispositivos (via NI-MAX) e um assistente para montar a
tabela de canais por tipo de sensor.

O caso do tio agrava: **cada obra/ensaio muda os canais** (quantos, quais sensores, calibração). Ele
precisa de algo que fique **salvo e reutilizável** entre ensaios, mas **editável** quando muda de
serviço — sem reconfigurar do zero toda vez, e sem abrir arquivos soltos.

A tentação a evitar (levantada na conversa de 02/07): guardar isso num **"cache/formato interno"** do
app. **Rejeitada** — ver Decisão 1.

## Decisão

### 1. O `.toml` continua sendo o formato de persistência (nada de cache interno)

"Salvo lá dentro" é **UX, não formato**. Por baixo, cada configuração continua sendo um `.toml`
legível. Três razões, específicas deste projeto:

- **O `.toml` já é o contrato de todo o backend** — `carregar_canais`, `AdaptadorDaqmx`, conversão,
  aferição ([ADR-002](002-conversao-linear-e-contrato-da-porta.md)/[ADR-006](006-calibracao-por-pontos.md)/[ADR-017](017-afericao-na-ui-e-escrita-de-config.md)/[ADR-020](020-parametros-de-strain-por-canal.md)).
  Um armazenamento paralelo reabriria decisões fechadas, sem ganho.
- **Rastreabilidade do laudo** — a configuração (sensor, calibração, gage factor) faz parte do
  documento técnico/legal do ensaio. Precisa ficar num arquivo legível e portável (o tio pode enviar
  "o config da Ponte X" quando algo der errado).
- **A escrita de config já existe** — `persistencia/config_canais.py` com `tomlkit`
  ([ADR-017](017-afericao-na-ui-e-escrita-de-config.md)) preserva comentários/formatação. É reuso.

### 2. Biblioteca de perfis (o que o tio chama de "versões")

O app gerencia uma **pasta-padrão de configurações** (o tio nunca navega até ela). Cada configuração
é um `.toml` nomeado por **obra/ensaio** ("Ponte Rio–Niterói", "Laje bloco B"). A UI **lista, cria,
duplica, renomeia, edita e remove** perfis — o tio escolhe por **nome amigável**, não por caminho.
Trocar de ensaio = trocar/duplicar perfil; ficar no mesmo = o perfil (já aferido) continua ali.

### 3. Editor de canais na UI (CRUD), reusando a escrita TOML

Painel para **montar a tabela de canais pela tela**: adicionar/remover canal, com endereço físico,
**Nome do Sinal**, unidade, tipo (`tensao`/`strain`), conversão (linear/pontos) e os
`ParametrosStrain` quando strain ([ADR-020](020-parametros-de-strain-por-canal.md)). Grava via
`config_canais.py` estendido. Mantém a arquitetura **Presenter puro + Widget fino**
([ADR-015](015-ux-e-fluxo-do-dashboard.md)) — a lógica de montar/validar o perfil é testável no Mac
sem display; o widget só desenha.

### 4. Discovery de dispositivos atrás da porta (opcional)

O "ele já reconhecia tudo": um comando **"Detectar canais do equipamento"** lista os
dispositivos/canais físicos do chassi conectado e preenche a tabela **sem digitar endereço**. Fica
**atrás da porta** (a `FonteDeAquisicao`, ou uma porta irmã de inventário): o `daqmx` implementa via
`nidaqmx.system.System.local().devices`; o `fake` devolve uma lista sintética (TDD no Mac). O
discovery é **opcional** — indisponível (Mac, ou driver ausente), o **editor manual** funciona
igual. Isso preserva a regra: `import nidaqmx` só no `daqmx.py`, lazy ([ADR-001](001-arquitetura-porta-adaptador.md)).

### 5. A tela inicial evolui para "gestor de ensaios"

O estado "Sem config" do [ADR-015](015-ux-e-fluxo-do-dashboard.md) deixa de ser só "Abrir arquivo" e
passa a **listar os perfis** (escolher / novo / editar). "Abrir um `.toml` avulso" continua como
escape (dev, ou importar um config que veio de fora). O resto do dashboard não muda.

### 6. Fatiar em duas partes (Mac agora, Windows depois)

- **Parte A** — biblioteca de perfis + editor de canais. **100% testável no Mac**, independe de
  hardware. É o que sobra de manual mesmo com o discovery.
- **Parte B** — discovery real. Só se valida no **Windows** (hardware/simulado). No Mac, só a
  montagem/escrita com fonte fake.

## Plano de fatias (ordem de execução, TDD)

Vertical, uma de cada vez — cada fatia entrega algo usável e testável antes da próxima.

**Parte A — no Mac, sem hardware:**

1. **A1 — Biblioteca de perfis (ler + selecionar).** A tela inicial lista os `.toml` da pasta-padrão
   por nome amigável e abre o escolhido no dashboard. Presenter puro (lista/seleção) + widget fino,
   reusando o `carregar_canais`. *De-risca a persistência e a tela inicial nova.*
2. **A2 — Editor de canais (CRUD) gravando `.toml`.** Adicionar/remover/editar canal (endereço, Nome
   do Sinal, unidade, tipo, conversão, `ParametrosStrain`) e salvar via `config_canais.py` estendido.
3. **A3 — Gerência de perfis.** Criar/duplicar/renomear/remover perfil na pasta-padrão; importar/
   exportar um `.toml` avulso.

**Parte B — precisa do Windows (hardware/simulado):**

1. **B — Discovery de dispositivos.** Porta de inventário (`daqmx` lista `System.local().devices`;
   `fake` lista sintética) e botão "Detectar canais" que preenche a tabela do editor. Só depois do
   feedback do tio ([ADR-019](019-foco-em-validacao-fisica-e-adocao.md)).

## Consequências

**Melhora:**

- Remove o último passo manual entre "recebeu o `.exe`" e "está adquirindo" — puxa forte a adoção
  (critério de sucesso do projeto).
- Reusa o `config_canais.py`/`tomlkit` e a arquitetura Presenter/Widget — pouco código novo de base.
- `.toml` legível/portável mantém a rastreabilidade do laudo e não quebra nada do backend.
- A Parte A entrega valor sozinha, no Mac, sem esperar acesso ao hardware.

**Piora / pendente:**

- **Escopo grande** — é uma fatia de UI nova; por isso o fatiamento A/B.
- **Discovery só valida no Windows** — o `fake` prova a montagem, não a lista real de devices.
- **Timing** — a Parte B não deve ser construída especulativamente antes do feedback do tio
  ([tarefas-futuras §4](../tarefas-futuras.md)); talvez o `.toml` pré-preenchido já baste no primeiro
  contato.
- Relação **perfil de config × metadata do ensaio** (`.meta.toml`, [ADR-018](018-metadata-do-ensaio.md))
  a definir (ver Pendências).

## Decisões de produto (resolvidas 02/07/2026)

Definidas com o Weslley — as recomendações do rascunho foram aceitas:

1. **Onde moram os perfis:** pasta-padrão gerenciada pelo app (caminho do usuário no SO, ex.:
   `Documentos/ensaios-ni/`), que o tio não precisa navegar — com **importar/exportar** um `.toml`
   avulso como escape.
2. **Discovery não é essencial no MVP:** a **Parte A** (editor manual + biblioteca de perfis) entra
   primeiro e já resolve o primeiro contato; o **discovery (Parte B)** vem depois do feedback do tio.
3. **Config e metadata seguem separados:** o perfil (`.toml`) guarda os canais; a metadata do ensaio
   continua no `.meta.toml` por ensaio ([ADR-018](018-metadata-do-ensaio.md)). A **obra é
   pré-preenchida** a partir do nome do perfil, sem fundir os dois arquivos.
4. **Validação no editor:** valida o essencial na hora (unidade e tipo obrigatórios, tipo ∈
   {`tensao`, `strain`}, número válido em ganho/offset/gage factor) para dar feedback imediato; o
   `carregar_canais` segue como a **rede de segurança final** (fonte única da regra — a UI só
   antecipa o aviso, não duplica a lógica).

   > **Refino (07/07/2026, do teste no Windows):** a "rede de segurança final" pegava **tarde demais**.
   > O editor **gravava** um canal incompleto (validação de escrita só do essencial: tipo + unidade) e o
   > `carregar_canais` só o rejeitava ao **reabrir** o perfil — o que **derrubava o app** (crash). Além
   > disso, um perfil com um canal inválido **travava a abertura** do editor. Correções: (a) o editor
   > **valida pela regra completa do domínio** (novo `validar_canal`, que reusa `_construir_canal`)
   > **antes** de gravar — recusa e **avisa**, sem gravar um canal que a releitura rejeitaria (decisão do
   > Weslley: **avisar e não gravar**, não dar default silencioso, pela mesma razão da armadilha do strain);
   > (b) a listagem e a reabertura do editor leem o TOML de forma **tolerante** (`EditorDeCanais.linhas`/
   > `campos`), para o editor **abrir mesmo com um canal inválido** no perfil, deixando o tio corrigir/
   > removê-lo; (c) TOML corrompido ao abrir o editor vira **aviso**, não traceback. Ver CHANGELOG (07/07).
