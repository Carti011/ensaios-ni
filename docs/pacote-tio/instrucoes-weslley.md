# Empacotar o `.exe` e enviar para o tio

Guia prático (para o Weslley) de como **gerar o executável no Windows** e **montar o pacote `.zip`**
que o tio recebe, descompacta e abre. É o passo que transforma "roda no meu Mac" em "o tio consegue
usar sozinho". Decisão de empacotamento: [ADR-022](../adr/022-empacotamento-exe-pyinstaller.md).

> **Onde cada coisa roda:** o `.exe` só se **gera no Windows** (é específico da plataforma; o Mac
> nem tem o `nidaqmx` para a coleta). Preparar o `.spec`, este guia e os arquivos que acompanham o
> zip é feito no Mac; **buildar é no Windows.**

---

## Visão geral (o fluxo inteiro)

```
[Windows] gerar o .exe  ──►  [Windows] testar o Iniciar no simulado  ──►  montar a pasta no Desktop  ──►  zipar  ──►  enviar
   pyinstaller                 (NI-MAX, sem o hardware do tio)             .exe + canais.toml + LEIA.txt
```

---

## Passo 1 — Preparar a máquina Windows (uma vez)

1. **Python 3.12** — `winget install Python.Python.3.12` (ou python.org, marcando *Add Python to PATH*).
2. **Driver NI-DAQmx** (gratuito, ni.com) — provavelmente já está instalado se a máquina roda o
   NI-MAX/FlexLogger. Traz o NI-MAX junto.
3. **Baixar o projeto** — `git clone <repo>` e entrar na pasta (`cd ensaios-ni`).
4. **Instalar com os extras de build:**
   ```
   pip install -e .[hardware,gui,excel,build]
   ```
   O extra `build` traz o PyInstaller; `hardware` = `nidaqmx`; `gui` = dashboard.
5. **Conferir a base:** `pytest` → deve dar **235 passed** (garante que o código está saudável nessa
   máquina antes de empacotar).

---

## Passo 2 — Gerar o `.exe`

A partir da **raiz do projeto**:

```
pyinstaller packaging/ensaios-ni.spec
```

Saída: **`dist\ensaios-ni.exe`** (arquivo único, ~66 MB, sem janela de terminal). É esse o arquivo
que o tio vai abrir.

> **Onde ele fica:** dentro da pasta **`dist\`** na raiz do projeto (ex.:
> `C:\...\ensaios-ni\dist\ensaios-ni.exe`). **Não** vai para a área de trabalho sozinho — você abre
> essa pasta e **copia** o `.exe` de lá para a pasta do Desktop no Passo 4.

> **Deu erro de módulo ausente** (comum com PySide6/pyqtgraph)? Acrescente o módulo em
> `hiddenimports` no `packaging/ensaios-ni.spec` e rode de novo. É o ciclo esperado do primeiro build
> (não aconteceu no build de 01/07, mas pode acontecer se a máquina for diferente). Ver
> [ADR-022](../adr/022-empacotamento-exe-pyinstaller.md).

**Rebuild:** toda vez que o **código mudar** (ex.: novas mensagens de erro), refaça o Passo 2 para o
`.exe` incluir a mudança. O `.exe` é uma foto do código no momento do build.

---

## Passo 3 — Testar o `.exe` antes de enviar (no seu Windows, sem o hardware do tio)

Este passo reduz o maior risco: o `.exe` empacotado **nunca** adquiriu dados (o Iniciar). Dá para
exercitar isso **sem o hardware do tio**, com **dispositivos simulados do NI-MAX**:

1. No NI-MAX, criar dispositivos simulados (chassi cDAQ-9184 + 2× 9205 + 1× 9235), se ainda não tiver.
2. Usar o **`config\canais-simulado.toml`** (já no projeto, 1 canal de strain) — confira no NI-MAX que
   o nome do device bate (default `cDAQ1Mod3`) e ajuste se for diferente.
3. Dar duplo-clique no `dist\ensaios-ni.exe` → "Abrir configuração…" → escolher o `canais-simulado.toml`.
4. **Clicar Iniciar.** Se o gráfico começar a correr com o sinal sintético, o elo
   empacotamento + aquisição **funciona** — a confiança de enviar sobe muito.

> No simulado o número é sintético (não é o físico real), mas o que se testa aqui é se o `.exe`
> **consegue carregar o driver e adquirir** — que é justamente o que faltava validar.

---

## Passo 4 — Montar a pasta no Desktop

Junte numa pasta única (ex.: **`Desktop\ensaios-ni-tio`**) os **três** arquivos:

| Arquivo | De onde vem | O que é |
| ------- | ----------- | ------- |
| `ensaios-ni.exe` | `dist\ensaios-ni.exe` (Passo 2) | o programa |
| `canais.toml` | copiar de `canais-exemplo.toml` (**nesta pasta**) e **preencher** | a configuração do ensaio |
| `LEIA.txt` | `LEIA.txt` (**nesta pasta**) | instruções para o tio |

**Preencher o `canais.toml` é o ponto que evita frustração.** A tela inicial pede esse arquivo antes
de abrir o dashboard. Duas opções:

- **Ideal:** preencher com os **canais reais** do tio (os nomes vêm do NI-MAX dele — ex.:
  `cDAQ9184-1820306Mod1/ai0`) e os sensores/unidades da obra. Aí o Iniciar já lê o hardware dele.
- **Mínimo (só para ele ver a cara do programa):** deixar o exemplo como está — o dashboard **monta**
  e ele navega, mas o **Iniciar** vai acusar canal inexistente (com a mensagem amigável explicando).

> O `canais.toml` real **não** é versionado no repositório (fica só na máquina) — cada obra tem o seu.

---

## Passo 5 — Zipar e enviar

Clicar com o botão direito na pasta `ensaios-ni-tio` → **Enviar para → Pasta compactada** (ou
"Compactar"). Isso gera `ensaios-ni-tio.zip` com os três arquivos dentro. **Sim — é só compactar a
pasta do Desktop.** Mandar esse `.zip` (WhatsApp/e-mail/nuvem). O tio descompacta e dá duplo-clique
no `ensaios-ni.exe`.

---

## Checklist antes de enviar

- [ ] `pytest` deu 235 passed na máquina de build.
- [ ] `dist\ensaios-ni.exe` foi gerado **depois** da última mudança de código.
- [ ] (recomendado) Iniciar testado no `.exe` com dispositivo simulado do NI-MAX.
- [ ] `canais.toml` preenchido (real ou exemplo) e copiado para a pasta.
- [ ] `LEIA.txt` na pasta.
- [ ] `.zip` gerado com os três arquivos **na raiz** (sem subpastas extras).

---

## O que o tio precisa na máquina dele

- **Driver NI-DAQmx** instalado (ele já tem, se usa o NI-MAX/FlexLogger). O `.exe` embute só o
  *wrapper* Python `nidaqmx`, **não** o driver nativo — por isso o driver é pré-requisito na máquina.
- **Windows 64-bit** (o `.exe` foi buildado para essa arquitetura).
- Nada de Python, `pip` ou linha de comando — o `.exe` é auto-contido.

Operação passo a passo no hardware (calibrar, tara, exportar): [guia-teste-hardware.md](../guia-teste-hardware.md).
