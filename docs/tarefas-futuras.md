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
