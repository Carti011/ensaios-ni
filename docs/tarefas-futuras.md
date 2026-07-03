# Tarefas futuras — ensaios-ni

Backlog de coisas que **não bloqueiam** o trabalho atual, mas devem ser feitas quando houver
oportunidade. Só o que está **pendente** fica aqui — o que foi concluído sai do arquivo e vive no
`CHANGELOG.md`/handoff/ADR correspondente.

---

## Urgências para a adoção (Fase 5–6)

> Estas pendências **decidem se o tio larga o FlexLogger** — têm prioridade sobre o resto. Por gravidade:

**🔴 Bloqueia a adoção (sem isto, o tio não usa):**

- [~] **Validar no hardware real** — validação **funcional** feita (29/06): o software lê o NI 9235
      real e responde à deformação. **Falta** a comparação numérica com o test panel do NI-MAX (mesma
      unidade, por **variação** carregado−repouso). Guia: [guia-teste-hardware.md](guia-teste-hardware.md). (Fase 5)
- [~] **Empacotar em `.exe`** — builda e o **`Iniciar` foi validado no simulado do NI-MAX** (02/07,
      após o fix do `copy_metadata`/`nitypes`). **Falta** o `Iniciar` no **hardware real do tio**.
      ([ADR-022](adr/022-empacotamento-exe-pyinstaller.md), Fase 6)
- [ ] **Validar o TXT no AqAnalysis** — ver §1 abaixo; é o elo da análise. Sem isto ele não fecha o
      trabalho.

**🟠 Ameaça a perfeição metrológica do laudo:**

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
- [ ] **A3 — Gerência de perfis.** Criar/duplicar/renomear/remover perfil na pasta-padrão;
      importar/exportar um `.toml` avulso.

**Parte B — precisa do Windows (hardware/simulado):**

- [ ] **B — Discovery de dispositivos.** Porta de inventário (`daqmx` lista `System.local().devices`;
      `fake` lista sintética) + botão "Detectar canais" que preenche a tabela do editor. Só depois do
      feedback do tio ([ADR-019](adr/019-foco-em-validacao-fisica-e-adocao.md)).

**Refinamentos menores da A2** (não bloqueiam):

- [ ] Exibir os números do formulário do canal em **decimal vírgula (BR)** (hoje o parse aceita
      vírgula e ponto, mas a exibição usa ponto).
- [ ] Validação **inline** no diálogo (desabilitar Aplicar até tipo/unidade válidos, à la
      `PainelAfericao`) — hoje avisa via popup ao aplicar.

---

## Outras pendências conhecidas (menores — já nos ADRs)

- [ ] **Excel "do jeito do tio"** — metadata no cabeçalho (obra, data, sensor, taxa), aba de resumo.
      Camada de entrega, a definir com o gosto dele. [ADR-011](adr/011-estrategia-de-exportacao.md).
- [ ] **Calibração "Ganho e Ponto de Referência"** — segundo modo de aferição do AqDados; redutível
      ao linear, baixa prioridade. [ADR-006](adr/006-calibracao-por-pontos.md).
