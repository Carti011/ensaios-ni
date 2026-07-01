# ADR 017 — Aferição na UI, escrita de config e nome do sinal (Fase 4, fatia 3)

## Status

**Aceito** (27/06/2026). Implementa a **fatia 3** do plano de fatias do
[ADR-015](015-ux-e-fluxo-do-dashboard.md) ("Aferição na UI") e **refina aquele plano** num ponto: a
tara sai do painel de aferição e vai para a fatia 4 (ver Decisão 5). Reusa a calibração por
regressão já decidida no [ADR-006](006-calibracao-por-pontos.md); a novidade é **UI + escrever o
TOML**, não lógica de cálculo. Não altera a arquitetura Presenter (puro) + Widget (PySide6 fino) do
ADR-015.

## Contexto

O backend de calibração já existia inteiro (regressão linear + correlação + tara no domínio,
ADR-006). Faltava o tio **aferir pela tela**, à la "Aferição por Regressão Linear" do AqDados
([referencia-lynx.md §1.2–1.3](../referencia-lynx.md)): montar a tabela de pontos `(V, valor eng.)`,
ver a reta e a **correlação %**, e **aplicar** — gravando a calibração na config. É a **primeira
vez que a UI escreve config** (até aqui só lia). Some-se a pendência do **nome do sinal**: a tabela
e os seletores X/Y mostravam o endereço físico (`Mod1/ai0`), que o tio não reconhece
([tarefas-futuras.md §3](../tarefas-futuras.md)).

## Decisão

### 1. A UI escreve o TOML com `tomlkit` (dependência core)

O `tomllib` da stdlib só lê. Para persistir a aferição **preservando comentários, formatação e os
demais canais** (o `canais.toml` é editado por humano), o escritor usa **`tomlkit`**, adicionado
como **dependência core** (`pyproject` `dependencies`) — primeira dep não-opcional do projeto.
Justificativa: escrever config é função do produto (não um add-on como `[excel]`/`[hardware]`/
`[gui]`), é leve e puro-Python (roda em ARM/Windows sem build) e dispensa a guarda-de-AST/lazy que o
`openpyxl` exige por ser pesado. O escritor vive em `persistencia/config_canais.py`
(`salvar_afericao`, `salvar_rotulo`, `ler_pontos`) — leitura de I/O fica na persistência; a
construção/validação do `Canal` segue no domínio (`carregar_canais`).

### 2. Só regressão linear + correlação na UI (sem segmento nem "Ganho e Ponto de Referência")

O painel afere por **regressão** (o padrão do ADR-006, espelhando o AqDados) e exibe **Ganho K**
(V/unidade), **Ganho 1/K** (unidade/V) e a **correlação %** ("100,00 %"), em decimal vírgula (BR) —
espelhando a tela "Aferição por Regressão Linear" do AqDados ([referencia-lynx.md §1.3](../referencia-lynx.md)).
A reta interna é `valor = a·V + b` com `a` = unidade/V (o "1/K"); o "K" é `1/a`. O método **segmento**
(opt-in, não-linear, raro) e o modo **"Ganho e Ponto de Referência"** (adiado no ADR-006) **não**
entram na UI desta fatia. Toda a UI é em **português** (os botões usam texto próprio, não os
`StandardButton` do Qt, que vêm em inglês). Mantém o painel enxuto e coerente com o já decidido.

### 3. Os pontos de calibração vivem no TOML, não no `Canal`

O `Canal` calibrado por regressão guarda **só a reta ajustada** (`reta`), não os pares `(V, valor)`
originais — a conversão não precisa deles. Para o painel **reabrir** uma aferição e mostrar os
pontos, eles são relidos do TOML (`ler_pontos`), que é a **fonte da verdade**. Decisão consciente de
**não inflar o `Canal`** com os pares só para a UI (evita um segundo significado para `Canal.pontos`,
hoje sinônimo de "método segmento").

### 4. Nome do sinal: `rotulo` no domínio, `etiqueta` como exibição, identidade separada no widget

O `Canal` ganhou o campo opcional **`rotulo`** (o "Nome do Sinal" do AqDados) e a property
**`etiqueta`** = `rotulo or nome` (cai no endereço físico quando não há rótulo). A UI exibe a
`etiqueta`; a **identidade** do canal (o endereço `Mod1/ai0`, que o DAQmx precisa) fica guardada à
parte no widget (`UserRole` na tabela, `itemData` nos combos X/Y). Assim a coluna de seleção pôde
deixar de usar o texto da célula como chave — o texto virou editável (renomear → `salvar_rotulo`).

### 5. A tara sai da fatia 3 e vai para a fatia 4

O ADR-015 listava "tara" no painel de aferição. **Decisão revisada:** a tara é **por-ensaio**
(lida do repouso no início, volátil — não persiste no `canais.toml`, conforme o ADR-006) e precisa
**estender o `MonitorAoVivo`** para capturar o repouso e tarar ao vivo. Isso pertence ao **controle
de ensaio (fatia 4)**, não à calibração persistida. A fatia 3 fecha com a **calibração**; a tara
entra na fatia 4 junto de Iniciar/Parar/duração.

### 6. Arquitetura mantida: Presenter puro + Widget fino

O Presenter `Afericao` (`apresentacao/afericao.py`) é Python puro (testável no Mac sem display):
pontos → `reta()` (reusa `ajustar_regressao`) → `correlacao_percentual()`, com `aplicar()`
persistindo via o escritor. O `PainelAfericao` (`apresentacao/qt/janela.py`) é um `QDialog` fino que
só desenha e fia eventos. Guardas de `nidaqmx` e `PySide6` intactas.

## Consequências

- **Backend quase intacto:** só o `Canal` ganhou `rotulo`/`etiqueta` e nasceu
  `persistencia/config_canais.py`. Domínio de conversão/regressão/aquisição não muda. **153 testes
  verdes** no Mac (smoke PySide headless + guardas de AST), sem `nidaqmx`.
- **Primeira dependência core** (`tomlkit`). `uv.lock` atualizado.
- **A UI escreve numa cópia de trabalho do exemplo** na demo do Mac (`_demonstracao` copia o
  `canais.exemplo.toml` versionado para um arquivo temporário) — a UI nunca grava no versionado.
- **Correlação arredondada** a 2 casas: pontos com leve dispersão podem exibir "100,00 %"
  (arredondamento), como no AqDados. Aceito.
- **Pendência aberta:** editar pontos exige re-aplicar para persistir (não há autosave) — proposital
  (o tio decide quando a calibração está boa). A validação de qualidade por um limiar de correlação
  foi **feita** em 01/07 (alerta abaixo de 95%, **avisa sem bloquear** — ver
  [ADR-006](006-calibracao-por-pontos.md)).
- **Próximo:** fatia 4 (metadata + exportar pela UI; e a **tara ao vivo** que veio para cá).
