# Guia de teste no hardware real (Fase 5) — do zero ao ensaio validado

Passo a passo para **validar o software no hardware de verdade do tio** (OFM Engenharia): chassi
**cDAQ-9184** + **2× NI 9205** (tensão) + **1× NI 9235** (strain), com os sensores reais (células de
carga, LVDTs, acelerômetros, extensômetros). Vai do ambiente zerado até um **ensaio completo,
calibrado e exportado**, na máquina dele.

> **Este é o guia único de campo.** Substitui os antigos `guia-windows.md` (instalação) e
> `validacao-windows.md` (validação no simulado) — eles foram fundidos aqui. O caso **simulado** (sem
> hardware, no Windows do dev) entra como **variante** no fim de cada passo, marcada com 🧪.
>
> **Por que ele importa:** o critério de sucesso do projeto é o tio **largar o FlexLogger**. Nada do
> que foi construído foi validado contra um sinal físico ainda — este guia é o que transforma
> "passa nos testes" em "funciona de verdade". Ver [avaliacao-critica.md](avaliacao-critica.md) §🔴1.

---

## Antes de ir (o que levar e conferir)

- [ ] Notebook com o repositório clonado **ou** acesso à máquina do tio para clonar lá.
- [ ] **Python 3.12+** (o `nidaqmx` exige 3.9+; o projeto fixa 3.12).
- [ ] **Driver NI-DAQmx** (gratuito, ni.com) instalado — já traz o **NI-MAX**.
- [ ] Cabo de rede para o chassi (o cDAQ-9184 é **Ethernet**; no setup do tio vai **direto no PC, IP
      fixo** — o número está no cofre privado, fora do repo).
- [ ] Saber **quais sensores estão em quais canais** e os **valores de calibração** (ou aplicar carga
      conhecida na hora). Sem isso o software lê, mas o número não significa nada.
- [ ] O **gage factor** dos extensômetros em uso (varia **2,14–2,16** por lote).
- [ ] Acesso ao **AqDAnalysis** do tio para validar a importação do TXT (passo 8).

---

## Passo 0 — Montar o ambiente (one-time, no Windows)

> Tem o Claude Code na máquina? Cole: *"Faça o onboarding deste projeto no Windows: confira o Python,
> instale com os extras de hardware e gui, rode os testes e me diga o que falta."* O resto é o manual.

1. **Python 3.12+** — `winget install Python.Python.3.12` (ou python.org marcando *Add Python to
   PATH*). Conferir: `python --version` → `Python 3.12.x`.
2. **Driver NI-DAQmx** — baixar em ni.com (gratuito), instalar (traz o NI-MAX). Abrir o NI-MAX.
3. **Baixar o projeto** — `git clone <repo>` e `cd ensaios-ni`. (Sem git: git-scm.com/download/win.)
4. **Instalar** — `pip install -e .[hardware,gui]` (hardware = `nidaqmx`; gui = dashboard).
5. **Conferir a base** — `pytest` → deve dar **203 passed** (confirma que o software está saudável
   nessa máquina, mesmo antes de tocar no hardware).

🧪 **Simulado (Windows do dev, sem hardware):** idem, mas no NI-MAX crie **dispositivos simulados**
(chassi cDAQ-9184 + 2× 9205 + 1× 9235) em vez de usar o chassi físico.

---

## Passo 1 — O chassi real aparece no NI-MAX

1. Ligar o chassi, conectar o cabo de rede, conferir o IP fixo.
2. No **NI-MAX**, em *Devices and Interfaces*, confirmar que o **cDAQ-9184** e os **3 módulos**
   aparecem (ex.: `cDAQ9184-1820306Mod1`, `Mod2`, `Mod3`).
3. **Anotar os nomes reais dos canais** (ex.: `cDAQ9184-1820306Mod1/ai0`) — vão para o `canais.toml`.
   Os nomes do simulado (`cDAQ1Mod1/ai0`) **não** são os do hardware real.

> **Não apareceu?** É rede/IP, não o software. Conferir cabo, IP fixo do chassi e firewall. O Python
> não entra aqui ainda.

---

## Passo 2 — Test panel do NI-MAX **antes** de qualquer Python

Esta é a **prova de que hardware + rede + sensor estão ok**, sem código no meio.

1. No NI-MAX, abrir o **test panel** de um canal de tensão (9205) e confirmar leitura coerente
   (mexer no sensor, ver o valor responder).
2. Abrir o test panel do **9235** (strain) e confirmar que responde sob carga conhecida.
3. **Guardar esses números** — eles são o **gabarito**: o nosso software tem que bater com eles.

> Este é o **critério objetivo de "funcionou"** de todo o projeto. Se o test panel não lê certo, o
> problema é hardware/fiação/sensor — resolver aqui antes de seguir.

---

## Passo 3 — Mapear os canais reais (`canais.toml`)

Copiar `config/canais.exemplo.toml` → `config/canais.toml` e preencher com os canais reais do NI-MAX.
O `canais.toml` real **não** é versionado (fica só na máquina). Cada obra/ensaio é um arquivo destes.

```toml
[canais."cDAQ9184-1820306Mod1/ai0"]
tipo = "tensao"
unidade = "kgf"
rotulo = "Carga"          # o "Nome do Sinal" do AqDados — o que o tio reconhece
ganho = 100.0             # provisório: será substituído pela aferição (passo 6)
offset = 0.0

[canais."cDAQ9184-1820306Mod3/ai0"]
tipo = "strain"           # task separada, parâmetros do 9235 (quarter-bridge/120/2,0)
unidade = "µε"
rotulo = "Sg1 bico"
ganho = 1000000.0         # strain → microstrain
offset = 0.0
```

---

## Passo 4 — Validar a leitura do software contra o test panel

A leitura finita do nosso software tem que **bater** com o número do test panel (passo 2).

```text
python -m ensaios_ni --fonte daqmx --config config/canais.toml --taxa 1024 --amostras 1024 --saida validacao-finita.csv
```

**Aprovação:**
- [ ] Rodou **sem erro** e gravou o CSV.
- [ ] O CSV tem a coluna de tensão **e** a de microstrain (µε), com `tempo_s`.
- [ ] Com uma **carga conhecida** aplicada, o valor lido **bate com o test panel do NI-MAX** no mesmo
      canal. **Este é o teste que nunca foi feito** — é o que de fato valida o projeto.

🧪 **Simulado:** o dispositivo gera senoide/ruído sintético — dá para confirmar que **lê sem erro**,
mas **não** o número físico (não há sinal real). O número físico só fecha aqui, no hardware.

---

## Passo 5 — Conferir a armadilha do strain (9235)

No test panel do 9235 (ou nas propriedades da task), confirmar que a leitura usa **quarter-bridge,
120 Ω, 2,0 V** — **nunca** full-bridge 350 Ω / 2,5 V (os defaults da API, que dão **número plausível
e errado, sem erro**). O teste-guarda automatizado já trava isso no código; aqui se confirma no driver
real. Ver [contexto-hardware.md §4](contexto-hardware.md) e [ADR-009](adr/009-leitura-de-strain-9235.md).

- [ ] Conferir o **gage factor** real do extensômetro em uso (2,14–2,16) — ajustar se necessário.

---

## Passo 6 — Calibrar um sensor real (aferição pela UI)

Abrir o dashboard **ligado ao hardware** (lê o `canais.toml` real, não a demo sintética) e aferir um
canal à la AqDados (pontos → reta → correlação):

```text
python -m ensaios_ni.apresentacao.qt.hardware --config config/canais.toml --taxa 1024 --bloco 256
```

> Este é o launcher de campo: abre o dashboard completo (Aferir, Zerar, metadata, Exportar) sobre o
> `AdaptadorDaqmx`. Config ausente/inválido vira mensagem clara, sem traceback. (O
> `...qt.janela` continua existindo, mas é a **demo com o adaptador `fake`** — sem hardware.)

1. Selecionar o canal → **Aferir…**.
2. Para cada ponto: aplicar uma **carga conhecida** e clicar **"Capturar tensão"** (o "Leitura do A/D"
   do AqDados) — a tensão lida ao vivo entra na tabela; digite o **Valor de engenharia** (a carga
   aplicada) ao lado. Repita com cargas **diferentes** (a tensão precisa variar entre os pontos).
3. Conferir o **Ganho K**, o **1/K** e a **correlação %** (quanto mais perto de 100%, melhor a reta).
   Abaixo de **95%** o painel avisa; se as tensões saírem iguais, ele explica que faltam cargas
   distintas (e o Aplicar fica travado — proposital: não grava calibração inválida).
4. **Aplicar** — persiste no `canais.toml`. A nova calibração vale do próximo **Iniciar**.

> **Só no hardware.** A captura ao vivo lê a tensão **atual** do canal. No Mac com o `fake` o sinal é
> sintético e sua média é constante, então **capturar ali dá sempre a mesma tensão** — o fluxo de
> captura só se exercita de verdade aqui, aplicando cargas físicas distintas. No Mac, para testar a
> aferição, digite os pontos à mão.

---

## Passo 7 — Tara (zero) com a peça em repouso

Com a peça **em repouso** e o ensaio rodando, clicar **Zerar**: o próximo bloco vira o zero dos
canais (Zero Channel). A tara é **por-ensaio** — cada Iniciar recomeça sem zero.

- [ ] Em repouso, após Zerar, a leitura tarada fica **em torno de zero**.

---

## Passo 8 — Rodar um ensaio real completo e exportar

1. Preencher a **metadata** no topo (obra, operador, data) — vai para o laudo.
2. **Iniciar** o ensaio (estático: ver o XY carga × deformação; dinâmico: ver o sinal de vibração).
3. **Parar** — grava o CSV + o `.meta.toml` ao lado.
4. **Exportar…** → escolher formato, sinais e janela de tempo.
5. **Validar o TXT no AqAnalysis dele:** exportar `txt-aqanalysis` e **importar no AqDAnalysis do tio**
   ("Ferramentas → Importa Arquivo Texto"). Conferir separador, decimal (vírgula) e cabeçalho.

> ⚠️ **Crítico (ver [avaliacao-critica.md](avaliacao-critica.md) §🔴3):** o TXT é **provisório** e
> nunca foi importado de verdade. Se não entrar, ajustar separador/decimal/cabeçalho no wizard de
> importação e calibrar o exportador (é plugável — o ajuste é trivial). **Sem isto, o tio não fecha o
> ciclo de análise.** Ver [tarefas-futuras.md §1](tarefas-futuras.md) e [ADR-011](adr/011-estrategia-de-exportacao.md).

---

## Passo 9 — Aquisição contínua / longa duração

Para ensaios longos (o tio faz de 1 h a 1 ano):

```text
python -m ensaios_ni --continuo --fonte daqmx --config config/canais.toml --taxa 1024 --bloco 256 --duracao-s 10 --saida validacao-continua.csv
```

**Aprovação:**
- [ ] Encerra por **duração** (ou por **Ctrl-C**) gravando o CSV; o `tempo_s` é **contínuo e
      crescente** (sem reiniciar a cada bloco).

> ⚠️ **Limite conhecido (ver [avaliacao-critica.md](avaliacao-critica.md) §🟡8):** um ensaio de meses
> num único CSV é inviável (volume + memória + queda de rede). Para teste curto está ok; monitoramento
> real de longa duração exige rotação de arquivo e recuperação de rede (pendente).

---

## Checklist de aprovação da Fase 5

| Validação | Critério |
| --------- | -------- |
| Chassi no NI-MAX | cDAQ-9184 + 3 módulos aparecem; nomes anotados |
| Test panel | cada canal lê coerente sob sinal conhecido |
| Leitura do software | **bate com o test panel** (o número físico) |
| Armadilha do strain | quarter-bridge 120 Ω / 2,0 V confirmado no driver |
| Calibração real | reta + correlação alta num sensor de verdade |
| Tara | em repouso, leitura tarada ≈ zero |
| Ensaio completo | grava CSV + metadata; dashboard mostra ao vivo |
| **TXT no AqAnalysis** | **importa no AqDAnalysis do tio** |
| Contínuo | encerra limpo, tempo contínuo |

Com o número físico batendo e o TXT importando, a Fase 5 está validada. O que sobra é a Fase 6
(empacotar em `.exe` e adoção) — ver [roadmap.md](roadmap.md).

---

## Empacotar o `.exe` (Fase 6) — no Windows

Para o tio abrir por um **ícone**, sem Python nem linha de comando. O binário é específico da
plataforma: **gera-se no Windows** (ver [ADR-022](adr/022-empacotamento-exe-pyinstaller.md)).

Pré-requisitos na máquina de build (uma vez):

- Python 3.12 + driver NI-DAQmx (os mesmos do Passo 0).
- `pip install -e .[hardware,gui,excel,build]` — o extra `build` traz o PyInstaller.

Gerar, a partir da **raiz do projeto**:

```text
pyinstaller packaging/ensaios-ni.spec
```

Saída: **`dist/ensaios-ni.exe`** (arquivo único). Copiar para a máquina do tio.

**Aprovação:**

- [ ] Duplo-clique abre a **tela inicial** ("Abrir configuração…"), **sem** janela de terminal.
- [ ] Escolher um `canais.toml` monta o dashboard.
- [ ] **Iniciar** lê o hardware — exige o **driver NI-DAQmx** instalado na máquina do tio (o `.exe`
      traz só o wrapper Python `nidaqmx`, não o driver nativo).

> Build falhou por módulo ausente (comum com PySide6/pyqtgraph)? Acrescentar o módulo em
> `hiddenimports` no `packaging/ensaios-ni.spec` e rebuildar. É o ciclo esperado do primeiro build
> ([ADR-022](adr/022-empacotamento-exe-pyinstaller.md)).

---

## Se algo não bater (troubleshooting)

- **Chassi não aparece no NI-MAX** → rede/IP/cabo/firewall (não é o software).
- **9235 falha na leitura** (`on-demand`) → precisa de **sample clock explícito**; o código já
  configura — se falhar, é a task/timing. Ver [contexto-hardware.md §3](contexto-hardware.md).
- **Strain absurdo mas sem erro** → quase certo que caiu nos **defaults da API** (full-bridge 350 Ω):
  conferir o passo 5.
- **Número de tensão não bate com o test panel** → escala/calibração (passo 6) ou faixa/terminal
  (DIFF × RSE conforme a fiação real).
- **TXT não importa no AqAnalysis** → ajustar separador/decimal/cabeçalho no wizard; calibrar o
  exportador `txt-aqanalysis` ([tarefas-futuras.md §1](tarefas-futuras.md)).

Detalhe técnico do hardware e a API pinada do `nidaqmx`: [contexto-hardware.md](contexto-hardware.md).
Como **operar** o software no dia a dia (CLI, exportação): [uso.md](uso.md).
