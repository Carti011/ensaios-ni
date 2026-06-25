# ADR 011 — Estratégia de exportação e interoperabilidade com o AqDAnalysis (TXT)

## Status

Aceito (24/06/2026). A camada de exportadores foi detalhada e implementada pelo
[ADR-012](012-serie-temporal-e-exportadores.md) (25/06/2026): `SerieTemporal` + `carregar_csv` e os
exportadores **CSV-Excel-BR** e **`.xlsx`** (com seleção de sinais). O exportador **TXT** segue
pendente do layout do "Importa Arquivo Texto".

## Contexto

O dono usa o **AqDAnalysis** (Lynx) para toda a análise — FFT (Auto Espectro), fadiga (Rainflow,
Markov), espectro cruzado, função de transferência, filtragem de spikes, relatórios técnicos. É uma
suíte madura (ver [referencia-lynx.md §2](../referencia-lynx.md)). Surgiu a pergunta: o nosso
software deve **reescrever** essa análise, ou **interoperar** com ela?

Fatos sobre os formatos de arquivo (confirmados pelo dono em 23/06/2026):

- O AqDados grava em **`.LDT`**, formato **proprietário sem especificação pública**; só o
  AqDAnalysis abre. **Inviável gerar.**
- O AqDAnalysis **importa e exporta TXT** (menu Ferramentas → "Importa Arquivo Texto").
- Formatos como `.BIN` (Catman), `.MEA` (MGCPlus) são **binários estruturados**: a extensão é só um
  rótulo; renomear um CSV para `.BIN` **não funciona** porque o leitor espera uma estrutura de bytes
  específica. Interoperar exige **converter o conteúdo** para o layout-alvo, não trocar a extensão.

O que importa para o dono (palavras do Weslley): *"o único importante é funcionar para meu tio, ele
precisa conseguir executar o trabalho"*. Reescrever a suíte de análise da Lynx seria um projeto
inteiro e competiria com algo que ele já domina e gosta.

Há ainda um destino de saída além do AqDAnalysis: o dono **valoriza muito o Excel** ("ele fala
bastante sobre o Excel"; ficou empolgado ao ver outro software entregar dados "já no formato do
Excel"). Logo, exportar para Excel é requisito de produto, não só de análise.

## Decisão

**O nosso software foca em aquisição + calibração + gravação. A análise fica com o AqDAnalysis, via
exportação de TXT.** Não reescrevemos a suíte de análise da Lynx.

- **Camada de exportadores plugáveis.** A mesma série temporal em memória (resultado do ensaio)
  alimenta múltiplos formatos de saída, cada um uma rotina de escrita independente:
  - **CSV legível** — formato atual, genérico (já existe em `persistencia/csv_ensaio.py`).
  - **TXT para o AqDAnalysis** — no layout que o "Importa Arquivo Texto" aceita. A implementar.
  - **Excel** — o dono valoriza muito abrir os dados no Excel. Dois níveis:
    - **CSV "amigável ao Excel BR"**: separador `;` e **decimal com vírgula** (no Excel em português
      o separador de lista é `;` e o decimal é `,`; um CSV com `,`/`.` abre tudo numa coluna só).
      Pode ser uma variante/opção do exportador CSV.
    - **`.xlsx` nativo** (via `openpyxl`): o arquivo do Excel "de verdade", com cabeçalho/unidades
      formatados — é o "já vem no formato do Excel" que encanta o dono. Adiciona dependência
      (`openpyxl`), provavelmente como extra opcional no `pyproject` (não pesa no domínio).
  - Outros formatos só quando houver necessidade real (sem especular).
- **Seletividade de exportação.** Nem todo canal/coluna precisa ir para todo arquivo — o exportador
  deve permitir escolher **quais sinais** exportar (pedido do dono: "nem todos são importantes
  colocar lá"). Detalhe de implementação do exportador.
- **Não geramos `.LDT`** (proprietário) nem fingimos formatos binários renomeando extensão.
- A interoperabilidade é por **conteúdo convertido**, não por renomear arquivo.
- **Análise própria (FFT etc.) é, no máximo, visualização ao vivo no dashboard** (Fase 3), nunca um
  substituto da suíte do AqDAnalysis. A análise "de verdade" continua sendo feita lá pelo dono.

## Consequências

**Melhora:**

- Escopo drasticamente menor: entregamos valor (aquisição que funciona) sem reescrever anos de
  engenharia de análise.
- O dono usa a ferramenta de análise que **já domina**, com os dados do **nosso** software de
  aquisição — melhor dos dois mundos.
- Arquitetura de exportadores deixa fácil adicionar formatos depois sem tocar no domínio.

**Piora / pendente:**

- **Incógnita do layout do TXT.** É preciso descobrir o formato exato que o "Importa Arquivo Texto"
  do AqDAnalysis aceita: separador (tab/`;`/espaço), cabeçalho, linha de taxa de amostragem, número
  de colunas, e **decimal com vírgula** (padrão BR/Lynx — as telas mostram `1,2241`). Fechar testando
  no Windows com o AqDAnalysis ou na documentação da Lynx. Não bloqueia a aquisição; bloqueia só o
  exportador TXT.
- Dependência de uma ferramenta de terceiro (AqDAnalysis) para a análise — aceitável, porque é a que
  o dono quer usar. Se um dia ele quiser análise dentro do nosso software, vira um novo ADR.
- O `.xlsx` nativo adiciona a dependência **`openpyxl`** — manter como extra opcional do
  `pyproject` para não pesar no domínio testável no Mac. O CSV-amigável-ao-Excel não adiciona
  dependência (só configura separador/decimal) e cobre o caso básico.
