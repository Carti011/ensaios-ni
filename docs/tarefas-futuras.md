# Tarefas futuras — ensaios-ni

Backlog de coisas que **não bloqueiam** o trabalho atual, mas devem ser feitas quando houver
oportunidade. Não esquecer. Marcar `[x]` quando concluída e mover o aprendizado para o ADR/handoff
correspondente.

---

## Urgências para a adoção (Fase 5–6)

> Consolidado da [avaliacao-critica.md](avaliacao-critica.md) (28/06/2026). Estas pendências **decidem
> se o tio larga o FlexLogger** — têm prioridade sobre o resto do backlog. Por gravidade:

**🔴 Bloqueia a adoção (sem isto, o tio não usa):**

- [~] **Validar no hardware real** — **validação FUNCIONAL feita (29/06/2026):** o software lê o NI
      9235 real e responde à deformação aplicada (força na chapa → gráfico coerente com a direção).
      **Falta** a comparação numérica fina com o test panel do NI-MAX (mesma unidade, por **variação**
      carregado−repouso) e validar o TXT no AqDAnalysis. Guia:
      [guia-teste-hardware.md](guia-teste-hardware.md). (Fase 5)
- [ ] **Empacotar em `.exe`** (PyInstaller) — o tio não roda `pip install`; hoje o programa **não
      abre** na máquina dele. (Fase 6)
- [ ] **Validar o TXT no AqAnalysis** — ver §1 abaixo; é o elo da análise. Sem isto ele não fecha o
      trabalho.

**🟠 Ameaça a perfeição metrológica do laudo:**

- [ ] **Sincronização tensão × strain (start-trigger)** — o XY carga × deformação precisa dos canais
      **simultâneos**; hoje há offset entre tasks. Só valida no Windows.
      ([ADR-007](adr/007-aquisicao-continua.md)/[ADR-009](adr/009-leitura-de-strain-9235.md))
- [x] **Capturar a leitura ao vivo na aferição** — **feito (01/07/2026):** botão **"Capturar tensão"**
      no painel de aferição lê a tensão crua do canal ao vivo (`MonitorAoVivo.ler_tensao_atual`) e a
      insere na tabela; o operador só digita a carga conhecida — o "Leitura do A/D" do AqDados. Só em
      canais de tensão (célula de carga, LVDT, acelerômetro). Atende o **pedido direto do tio
      (30/06/2026):** *"falar pra ele [o software] que o valor de tensão que você está lendo é tal
      valor de engenharia"*. ([ADR-017](adr/017-afericao-na-ui-e-escrita-de-config.md))
- [x] **Alerta de correlação baixa na aferição** — **feito (01/07/2026):** correlação **abaixo de
      95%** pinta o indicador e mostra um aviso no painel de aferição, mas **não bloqueia** o Aplicar
      (o tio decide — como o resto do fluxo). Limiar = constante `Afericao.CORRELACAO_MINIMA`.
      ([ADR-006](adr/006-calibracao-por-pontos.md)/[ADR-017](adr/017-afericao-na-ui-e-escrita-de-config.md))

- [x] **Launcher do dashboard com hardware real** — **feito (30/06/2026):** novo entrypoint
      `apresentacao/qt/hardware.py` (`python -m ensaios_ni.apresentacao.qt.hardware --config
      canais.toml --taxa --bloco --saida --capacidade-janela`) abre o dashboard completo
      (metadata/exportar/tara/aferir) ligado ao `AdaptadorDaqmx(canais=...)`, repassando canais +
      config; config ausente/inválido/TOML quebrado vira mensagem amigável. O `...qt.janela` segue
      como demo `fake`. (Fase 5)

**🟡 Paridade total / robustez:**

- [ ] **FFT / frequência ao vivo** — o ensaio dinâmico (vibração 1024 Hz → frequências naturais) hoje
      depende de exportar pro AqDAnalysis; o FlexLogger tem **FFT ao vivo**. Decidir o escopo de
      "substituir totalmente" (precisa de um ADR-árbitro). [ADR-011](adr/011-estrategia-de-exportacao.md).
- [ ] **Robustez de longa duração** — rotação de arquivo + recuperação de queda de rede do chassi
      Ethernet; um ensaio de meses num único CSV é inviável (volume + memória). Inclui o **exportar
      ensaios gigantes pela entrada** (`carregar_csv` lê o CSV inteiro em memória).
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

## Outras pendências conhecidas (menores — já nos ADRs)

Não detalhadas aqui para não duplicar; o ADR é a fonte de verdade. As de maior impacto estão
consolidadas em **Urgências** no topo.

- [ ] **Mensagens de erro amigáveis na aquisição** — o `MonitorAoVivo.passo()` mostra o `str(erro)`
      cru no rótulo de estado (ex.: `No module named 'nidaqmx'` no Mac; falha de chassi/rede no
      Windows do tio). Traduzir para texto que o tio entenda (driver NI-DAQmx ausente, hardware não
      encontrado, canal inexistente). Polimento previsto na Fase 6 (ver [roadmap.md](roadmap.md)).
- [ ] **Excel "do jeito do tio"** — metadata no cabeçalho (obra, data, sensor, taxa), aba de resumo.
      Camada de entrega, a definir com o gosto dele. [ADR-011](adr/011-estrategia-de-exportacao.md).
- [ ] **Calibração "Ganho e Ponto de Referência"** — segundo modo de aferição do AqDados; redutível
      ao linear, baixa prioridade. [ADR-006](adr/006-calibracao-por-pontos.md).
- [x] ~~**Dashboard — decidir a stack**~~ → decidido: **PyQt6/pyqtgraph** ([ADR-013](adr/013-stack-do-dashboard.md)); construído na **Fase 4** (ver [roadmap.md](roadmap.md)).
