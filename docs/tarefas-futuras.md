# Tarefas futuras — ensaios-ni

Backlog de coisas que **não bloqueiam** o trabalho atual, mas devem ser feitas quando houver
oportunidade. Não esquecer. Marcar `[x]` quando concluída e mover o aprendizado para o ADR/handoff
correspondente.

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
      física) e tentar **importar o nosso TXT** no AqDAnalysis dele. Ver se entra; ajustar separador/
      decimal/cabeçalho no wizard de importação. É o teste definitivo (o critério de "funcionou").

> Expectativa fundamentada: o "Importa Arquivo Texto" do AqDAnalysis é quase certamente um **wizard
> configurável** (o usuário escolhe separador/decimal e aponta as colunas), padrão da indústria de
> software de aquisição. Se for, não há "formato secreto": o nosso TXT limpo + a escolha do tio no
> wizard bastam. A validação confirma isso.

## 2. Plano B — parametrizar o exportador TXT

Se a validação (tarefa 1) mostrar que o AqDAnalysis precisa de uma variante diferente, em vez de
fixar um novo formato, **tornar o `txt-aqanalysis` parametrizável**:

- [ ] separador configurável (`;` / TAB / espaço);
- [ ] separador decimal configurável (vírgula / ponto);
- [ ] opção de incluir a **taxa de amostragem no cabeçalho** (alguns importadores ASCII usam isso
      para reconstruir o eixo de tempo/frequência).

Assim, "acertar o formato" vira "gerar a variante que o wizard pedir", sem reescrever código.
Implementar **só quando a validação indicar necessidade** — não especular antes.

---

## 3. Nome do sinal (rótulo humano) nos canais — UI e config

Hoje a tabela de canais e os seletores X/Y do dashboard mostram o **endereço físico** do
canal (`Mod1/ai0` = "Módulo 1, entrada analógica 0"), que vem do NI-MAX/DAQmx. **O tio não
reconhece isso** — pra ele é como "tomada nº 1 da parede". Ele pensa no sensor pelo **que mede**:
"Carga", "Sg1 bico", "Sg2 reforço". O AqDados dele tem uma coluna **"Nome do Sinal"** (apelido
humano) **separada** do canal físico — ver [referencia-lynx.md](referencia-lynx.md) §1.1.

Causa raiz: o `Canal` (`dominio/canais.py`) só guarda o endereço físico (`nome`) + unidade; não
existe campo de rótulo, então a UI não tem o que exibir além do endereço. (Levantado em
26/06/2026, ao revisar o seletor XY da fatia 2 do dashboard.)

Como fechar (backend primeiro, frontend depois — commits separados):

- [x] **Backend** — campo opcional `rotulo` (nome do sinal) no `Canal` e no carregamento do
      TOML (`carregar_canais`), com **fallback** para o `nome` (endereço) via property `etiqueta`;
      validado como string. Documentado em `config/canais.exemplo.toml` e no `CONTEXT.md`.
- [x] **Frontend** — tabela (coluna "Sinal") e seletores X/Y exibem o **rótulo**, mantendo o
      endereço físico como identidade interna (`UserRole`/`itemData`). Editar o rótulo na tabela
      persiste no TOML (`salvar_rotulo`). Sem `rotulo`, cai no endereço.

> **Concluído na fatia 3 do dashboard (27/06/2026) — ver [ADR-017](adr/017-afericao-na-ui-e-escrita-de-config.md).**
> Era critério de **adoção**: o tio só reconhece o que ele nomeou (o "Nome do Sinal" do AqDados).

---

## Outras pendências conhecidas (já registradas nos ADRs)

Não detalhadas aqui para não duplicar; o ADR é a fonte de verdade.

- [ ] **Exportar ensaios gigantes pelo lado da entrada** — `carregar_csv` ainda lê o CSV inteiro em
      memória; para reexportar um ensaio de meses, faltaria recortar a janela na leitura (ou
      streaming). [ADR-012](adr/012-serie-temporal-e-exportadores.md).
- [ ] **Excel "do jeito do tio"** — metadata no cabeçalho (obra, data, sensor, taxa), aba de resumo.
      Camada de entrega, a definir com o gosto dele. [ADR-011](adr/011-estrategia-de-exportacao.md).
- [ ] **Calibração "Ganho e Ponto de Referência"** — segundo modo de aferição do AqDados; redutível
      ao linear, baixa prioridade. [ADR-006](adr/006-calibracao-por-pontos.md).
- [x] ~~**Dashboard — decidir a stack**~~ → decidido: **PyQt6/pyqtgraph** ([ADR-013](adr/013-stack-do-dashboard.md)). A construção do dashboard é a **Fase 4** (ver [roadmap.md](roadmap.md)).
- [ ] **Análise própria (FFT) vs não reescrever análise** — tensão entre o ADR-011 e a visão de
      futuro; precisa de um árbitro (ADR) quando chegar no dashboard.
- [ ] **Sincronização por start-trigger** entre as tasks de tensão e strain — só valida no Windows.
      [ADR-007](adr/007-aquisicao-continua.md) / [ADR-009](adr/009-leitura-de-strain-9235.md).
- [ ] **Fase 5 — validação física** no hardware do tio (número real do strain, calibração),
      seguindo `docs/validacao-windows.md`.
