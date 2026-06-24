# ADR 008 — Paridade funcional com o FlexLogger

## Status

Aceito

## Contexto

O dono do hardware (OFM Engenharia) **já usa o FlexLogger** e está satisfeito com ele — o único
problema é a **assinatura paga**. A pilha que faz o hardware funcionar (NI-DAQmx + NI-MAX) é
gratuita; o FlexLogger é a camada de aplicação por cima, e é a única peça paga. Este projeto
reescreve **exatamente essa camada**.

Decorre disso uma diretriz de produto: se o software for **o mais parecido possível** com o
FlexLogger no modelo mental — mesma forma de calibrar, zerar e escalar sinais —, a transição pro
dono é trivial e ele não precisa reaprender nada. A pesquisa de 23/06/2026
([referencia-flexlogger.md](../referencia-flexlogger.md)) mostrou que o FlexLogger não inventa
conceitos próprios: ele expõe as **Custom Scales do NI-DAQmx**. Logo, "parecer com o FlexLogger"
e "seguir o padrão NI" são a mesma coisa — e ambos são gratuitos de adotar (são conceitos do
driver, não features proprietárias).

## Decisão

**A meta do projeto é fazer o hardware do tio funcionar sem custo de licença.** Ele já domina
o **NI-DAQmx** e o **NI-MAX** (ambos gratuitos) e a única peça que não quer pagar é o
**FlexLogger** (assinatura). Logo, na prática **estamos clonando o FlexLogger** — recriando a
camada de aplicação dele para que o tio tenha a sua, própria, e possa usar **sem pagar ninguém**.

Disso decorre um princípio que vale como atalho de decisão: **"parecer com o FlexLogger" e
"seguir o padrão NI-DAQmx" são a mesma coisa** — porque o FlexLogger não tem lógica proprietária
de conversão/medição; ele expõe os conceitos do driver (Custom Scales, zero, clip). Seguir o
padrão NI é, automaticamente, parecer com o FlexLogger, e é de graça.

**Espelhar o FlexLogger no modelo de domínio**, seguindo o padrão NI-DAQmx, com UX própria mais
moderna. Concretamente:

- **Escala/conversão:** adotar os tipos de **Custom Scale** do DAQmx — **Linear** (`y = m·x + b`)
  e **Table** (pontos com interpolação linear) como os dois suportados; Polynomial fica reservado.
  Ver [ADR-002](002-conversao-linear-e-contrato-da-porta.md) e [ADR-006](006-calibracao-por-pontos.md).
- **Zero/tara:** replicar o **"Zero Channel"** (média de um buffer vira offset), tratando-o como
  operação **separada da calibração**, como o FlexLogger faz.
- **Fora da faixa:** replicar o **clip (clamp)** que o DAQmx aplica na leitura por tabela.
- **Vocabulário e fluxo** alinhados aos do FlexLogger/AqDados (o dono já pensa nesses termos).
- **Formato de dados:** buscar compatibilidade com AqDados/AqDAnalysis (a confirmar com o dono).

**Regra operacional (vale para qualquer dúvida futura):** sempre que surgir uma dúvida de
comportamento ou uma decisão técnica ambígua (conversão, zero, faixa, timing, formato…),
**pesquisar primeiro como o FlexLogger/NI-DAQmx resolve** e adotar isso, em vez de inventar
comportamento próprio. Registrar o achado em [referencia-flexlogger.md](../referencia-flexlogger.md).
O FlexLogger é a referência objetiva de "o que é o correto" para este projeto.

**Escopo da paridade:** é paridade de **modelo mental e do caminho de medição** (configurar canal
→ escalar → zerar → adquirir → gravar), **não** paridade de feature-a-feature. O FlexLogger tem
dezenas de recursos que o dono não usa; não vamos clonar a aplicação inteira. A UX é nossa
(mais enxuta e moderna), só o comportamento técnico é fiel.

## Consequências

**Melhora:**

- Transição sem fricção pro dono — ele reconhece os conceitos.
- Cada decisão técnica ambígua passa a ter uma **referência objetiva** ("como o FlexLogger faz"),
  em vez de invenção própria. Reduz risco de número plausível e errado.
- Seguir o padrão NI-DAQmx mantém compatibilidade conceitual com o resto do ecossistema NI.

**Piora / pendente:**

- Exige pesquisar o comportamento do FlexLogger antes de decidir (custo de investigação).
- Paridade total seria escopo gigante — precisamos de disciplina pra parar no que o dono usa.
- Compatibilidade de **formato de arquivo** com AqDados/AqDAnalysis ainda não confirmada.
