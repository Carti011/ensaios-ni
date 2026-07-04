# Tarefas futuras — ensaios-ni

Backlog de coisas que **não bloqueiam** o trabalho atual, mas devem ser feitas quando houver
oportunidade. Só o que está **pendente** fica aqui — o que foi concluído sai do arquivo e vive no
`CHANGELOG.md`/handoff/ADR correspondente.

---

## Urgências para a adoção (Fase 5–6)

> Estas pendências **decidem se o tio larga o FlexLogger** — têm prioridade sobre o resto. Por gravidade:

### Feedback de campo — teste remoto do tio (03/07/2026)

O tio rodou o software sobre o **hardware real** dele (teste proposital com **um único módulo** — o
9235/strain) e mandou o retorno por áudio. Resumo do que ele reportou:

- ✅ **Funciona:** o software **lê**, **identifica a DAQ** e **leu a deformação** que ele aplicou na
  peça (o 9235). Palavras dele: "tá fazendo tudo perfeito, só precisa refinar".
- ⚠️ **Erro recorrente ao gravar (a arrumar):** **todo início de gravação dispara um erro** logo em
  seguida, de forma repetida — apesar dele, a leitura continua ("lê bonitinho"). O **texto exato do
  erro ainda é desconhecido** (falta print/mensagem — ver pergunta ao tio). → item 🔴 abaixo.
- 🟠 **Ver/capturar a tensão no canal de strain (decisão de produto):** o botão **"Capturar tensão"
  fica cinza** no canal de strain (é o design atual — a captura ao vivo é injetada só em canais de
  tensão/9205). O tio quer ver/capturar a **tensão crua do 9235** para inserir ponto de aferição e
  **correlacionar com o test panel do NI-MAX** (que mostra V/V), inclusive para investigar o erro
  acima. → item 🟠 abaixo.
- **Não é bug:** o software "identificar só um módulo" era **esperado** — o teste usou só um módulo de
  propósito.

> A confirmar com o Weslley: se esse teste rodou o **`.exe`** ou o `python -m` — se foi o `.exe` no
> hardware real, avança o status da Fase 6 no [roadmap.md](roadmap.md). Os áudios são material do tio
> (**não versionados**, conforme [onde-pesquisar.md](onde-pesquisar.md)); só esta análise textual fica
> no repo.

**🔴 Bloqueia a adoção (sem isto, o tio não usa):**

- [~] **Validar no hardware real** — validação **funcional** feita (29/06): o software lê o NI 9235
      real e responde à deformação. **Falta** a comparação numérica com o test panel do NI-MAX (mesma
      unidade, por **variação** carregado−repouso). Guia: [guia-teste-hardware.md](guia-teste-hardware.md). (Fase 5)
- [~] **Empacotar em `.exe`** — builda e o **`Iniciar` foi validado no simulado do NI-MAX** (02/07,
      após o fix do `copy_metadata`/`nitypes`). **Falta** o `Iniciar` no **hardware real do tio**.
      ([ADR-022](adr/022-empacotamento-exe-pyinstaller.md), Fase 6)
- [ ] **Validar o TXT no AqAnalysis** — ver §1 abaixo; é o elo da análise. Sem isto ele não fecha o
      trabalho.
- [ ] **Erro recorrente ao gravar no hardware do tio (03/07)** — no teste de campo, **todo início de
      gravação dispara um erro** logo em seguida, sempre; a leitura segue funcionando. Um erro que
      aparece "toda vez" mina a confiança do tio (e pode indicar gravação/parada mal encerrada). É
      **novo** — só apareceu no hardware/rede real, não no simulado. **Bloqueado por informação:**
      preciso do **texto/print do erro** (ver Perguntas ao tio) para diagnosticar. Hipóteses a
      investigar: timeout/buffer da task contínua do 9235 no chassi Ethernet
      ([contexto-hardware.md §3](contexto-hardware.md)); erro no encerramento/parada da gravação; ou
      um `DaqError` que a tradução amigável ([apresentacao/erros.py](../src/ensaios_ni/apresentacao/erros.py))
      ainda não cobre. Diagnóstico disciplinado com `/diagnose` quando houver o texto do erro.

**🟠 Ameaça a perfeição metrológica do laudo:**

- [ ] **Ver/capturar a tensão (razão de ponte V/V) do canal de strain (9235)** — pedido direto do tio
      (03/07). Hoje o "Capturar tensão" da aferição é injetado **só em canais de tensão** (9205) e fica
      **cinza** no strain, porque o 9235 entrega **strain** direto (via `add_ai_strain_gage_chan`, com
      gage factor e quarter-bridge aplicados no driver) e strain não se afere por pontos de tensão.
      **Mas há um "número de tensão" real no 9235:** o módulo é **ratiométrico** — mede a **razão de
      ponte V/V** (`Vr = (Vch/Vex)carregado − (Vch/Vex)repouso`, faixa ±29,4 mV/V), da qual o strain é
      derivado. Essa razão V/V é **o que o test panel do NI-MAX mostra** — logo, expô-la resolveria a
      **correlação NI-MAX × software** (hoje travada por unidades diferentes: V/V no NI-MAX × µε no
      software, o "ajuste fino" pendente da validação física da Fase 5) e daria ao tio o que ele pediu
      para diagnosticar o erro. Caminho técnico: ler a razão de ponte via **`BridgeUnits`/canal de bridge**
      do `nidaqmx` — **assinatura exata a confirmar contra a doc oficial e o NI-MAX no Windows** (regra:
      não inventar assinatura, [contexto-hardware.md §4](contexto-hardware.md)). **Decisão de produto
      pendente:** (a) habilitar a captura de V/V no strain (para aferição/diagnóstico), ou (b) só um
      *display* de V/V ao lado do µε, ou (c) manter cinza e explicar ao tio por que strain já vem
      calibrado. Refina [ADR-017](adr/017-afericao-na-ui-e-escrita-de-config.md)/[ADR-020](adr/020-parametros-de-strain-por-canal.md);
      pode virar ADR se a leitura de V/V entrar na porta.
- [ ] **Sincronização tensão × strain (start-trigger)** — o XY carga × deformação precisa dos canais
      **simultâneos**; hoje há offset entre tasks. Só valida no Windows.
      ([ADR-007](adr/007-aquisicao-continua.md)/[ADR-009](adr/009-leitura-de-strain-9235.md))

**🟡 Paridade total / robustez:**

- [~] **FFT / frequência ao vivo** — escopo decidido ([ADR-021](adr/021-fft-ao-vivo-paridade-dinamica.md)):
      FFT ao vivo no dashboard, substituindo o FlexLogger também no dinâmico. É a **Fase 7**
      ([roadmap.md](roadmap.md)), **depois** do `.exe`. Análise pesada segue no AqDAnalysis via TXT.
- [ ] **Robustez de longa duração** — rotação de arquivo + recuperação de queda de rede do chassi
      Ethernet; um ensaio de meses num único CSV é inviável (volume + memória). Inclui exportar
      ensaios gigantes (o `carregar_csv` lê o CSV inteiro em memória).
      [ADR-012](adr/012-serie-temporal-e-exportadores.md).

---

## 1. Validar o exportador TXT-AqAnalysis (formato provisório)

O exportador `txt-aqanalysis` está implementado de forma **provisória** (decimal vírgula confirmado;
separador TAB, encoding utf-8 e cabeçalho de uma linha são escolhas a confirmar). Ver
[ADR-011](adr/011-estrategia-de-exportacao.md) e o comentário no topo de
`src/ensaios_ni/persistencia/exportadores/txt_aqanalysis.py`.

Como fechar (qualquer uma das vias valida):

- [ ] **Via A — TXT legítimo do tio.** O tio exporta um TXT qualquer no AqDAnalysis e envia. Com um
      arquivo real em mãos, comparo o layout (separador, encoding, cabeçalho, nomes de unidade) e
      ajusto o exportador para casar. **O Weslley já pediu o arquivo a ele (25/06/2026) e aguarda.**
- [ ] **Via B — testar na casa do tio.** Ir ao computador do tio (Fase 5, junto da calibração
      física) e tentar **importar o nosso TXT** no AqDAnalysis dele. Ajustar separador/decimal/
      cabeçalho no wizard de importação. É o teste definitivo (o critério de "funcionou").

> Expectativa fundamentada: o "Importa Arquivo Texto" do AqDAnalysis é quase certamente um **wizard
> configurável** (escolhe separador/decimal e aponta as colunas). Se for, não há "formato secreto":
> o nosso TXT limpo + a escolha do tio no wizard bastam.

## 2. Plano B — parametrizar o exportador TXT

Se a validação (tarefa 1) mostrar que o AqDAnalysis precisa de uma variante diferente, em vez de
fixar um novo formato, **tornar o `txt-aqanalysis` parametrizável**:

- [ ] separador configurável (`;` / TAB / espaço);
- [ ] separador decimal configurável (vírgula / ponto);
- [ ] opção de incluir a **taxa de amostragem no cabeçalho** (alguns importadores ASCII usam isso
      para reconstruir o eixo de tempo/frequência).

Implementar **só quando a validação indicar necessidade** — não especular antes.

---

## 3. Configuração de canais na UI ([ADR-023](adr/023-configuracao-de-canais-na-ui.md)) — em andamento

O tio não deve editar o `canais.toml` à mão. Design fechado no ADR-023: biblioteca de **perfis**
`.toml` gerenciada pelo app + **editor** de canais na tela + **discovery** dos dispositivos atrás da
porta. Fatiado; estado atual:

**Parte A — no Mac:**

- [x] **A1 — Biblioteca de perfis.** A tela inicial lista os ensaios salvos (`~/ensaios-ni/*.toml`) e
      abre o escolhido. (`apresentacao/perfis.py` + `TelaInicial`.)
- [x] **A2 — Editor de canais.** Tabela de canais na UI (Adicionar/Editar/Remover) + formulário por
      canal, persistindo no `.toml`. (`apresentacao/editor_canais.py` + `qt/editor_canais.py`.)
- [x] **A3 — Gerência de perfis (completa, 04/07).** Criar, Importar, Renomear, Remover, Duplicar e
      Exportar — todos pela tela, com validação de nome e erros de domínio
      (`PerfilJaExiste`/`PerfilNaoExiste`/`NomeDePerfilInvalido`/`ImportacaoInvalida`). **Fecha a
      Parte A do [ADR-023](adr/023-configuracao-de-canais-na-ui.md)** (biblioteca + editor + gerência);
      a biblioteca não nasce mais vazia numa máquina nova.

**Parte B — precisa do Windows (hardware/simulado):**

- [ ] **B — Discovery de dispositivos.** Porta de inventário (`daqmx` lista `System.local().devices`;
      `fake` lista sintética) + botão "Detectar canais" que preenche a tabela do editor. Só depois do
      feedback do tio ([ADR-019](adr/019-foco-em-validacao-fisica-e-adocao.md)).

**Refinamentos menores da A2** (não bloqueiam):

- [x] **Botão "Editar canais…" não dava feedback sem perfil selecionado** (descoberto no Windows,
      03/07; **corrigido em 04/07**). O botão nasce **desabilitado** e habilita ao selecionar um
      ensaio (`currentItemChanged` → `_sincronizar_botoes`), como o "Aferir".
- [x] **UX da tela inicial com muitos botões** — **resolvido (04/07):** a tela foi reorganizada em
      **dois grupos** (ações do ensaio selecionado × ações da biblioteca/avulso), em vez de uma fileira
      única. Resta a ambiguidade menor entre "Importar…" (adota na biblioteca) e "Abrir configuração…"
      (abre avulso) — aceitável por ora; fundir num fluxo só é opção futura, não bloqueia.
- [ ] Exibir os números do formulário do canal em **decimal vírgula (BR)** (hoje o parse aceita
      vírgula e ponto, mas a exibição usa ponto).
- [ ] Validação **inline** no diálogo (desabilitar Aplicar até tipo/unidade válidos, à la
      `PainelAfericao`) — hoje avisa via popup ao aplicar.

---

## Outras pendências conhecidas (menores)

- [ ] **Guia de uso dentro do app para o tio (README/tutorial)** — instruções em linguagem leiga de
      como operar o programa (criar/importar ensaio, editar canais, aferir, tarar, iniciar, exportar),
      acessível **de dentro do app** (ex.: botão "Ajuda"/"Como usar") ou junto do `.exe`. Complementa o
      `LEIA.txt` do [pacote-tio](pacote-tio/README.md), que hoje só cobre abrir o programa. **Para mais
      pra frente** (pedido do Weslley, 04/07) — não agora.
- [ ] **Excel "do jeito do tio"** — metadata no cabeçalho (obra, data, sensor, taxa), aba de resumo.
      Camada de entrega, a definir com o gosto dele. [ADR-011](adr/011-estrategia-de-exportacao.md).
- [ ] **Calibração "Ganho e Ponto de Referência"** — segundo modo de aferição do AqDados; redutível
      ao linear, baixa prioridade. [ADR-006](adr/006-calibracao-por-pontos.md).
