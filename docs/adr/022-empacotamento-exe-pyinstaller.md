# ADR 022 — Empacotamento em executável Windows (PyInstaller)

## Status

Aceito (01/07/2026). Implementa a **distribuição** da [Fase 6](../roadmap.md) (empacotamento &
adoção). O `.spec` e o guia são preparados no Mac; **o binário só se gera e valida no Windows**.

> **Validado no Windows (01/07/2026).** `pyinstaller packaging/ensaios-ni.spec` gerou
> `dist/ensaios-ni.exe` (65,9 MB, one-file, sem console) **sem ajuste** no `.spec`. A tela inicial
> abre e o dashboard monta com o `canais.exemplo.toml` (5 canais, sub-plots, XY, controles); 214
> testes verdes no Windows. Startup rápido nas aberturas normais (o cold-start da 1ª descompressão
> pode demorar). Único aviso: `pyqtgraph.opengl` sem `PyOpenGL` — inofensivo (só usamos 2D; entra em
> cena se a Fase 7/FFT precisar de 3D). Falta o **Iniciar** no hardware do tio (driver + chassi).

## Contexto

O critério de sucesso é o tio **largar o FlexLogger** — mas hoje **o programa não abre na máquina
dele**: ele não roda `pip install`, não tem Python configurado, não mexe em linha de comando. Esse é
o **bloqueador nº 1 da adoção** (ver a reavaliação de rota no [roadmap.md](../roadmap.md)). Sem um executável clicável, todo o resto
(dashboard, aferição, exportadores) é inalcançável para ele.

O pré-requisito de UX já foi feito em 01/07: a **tela inicial sem CLI** (`qt.hardware` → botão
"Abrir configuração…"), justamente para o tio abrir por um ícone e escolher o `canais.toml`, sem
digitar nada.

## Decisão

Empacotar com **PyInstaller** num executável Windows. Escolhas:

- **Entrypoint = `src/ensaios_ni/apresentacao/qt/hardware.py`** (a tela inicial sem CLI). É o
  programa "de verdade" ligado ao `AdaptadorDaqmx`, não a demo `fake` (`qt/janela.py`).
- **one-file** (um único `.exe`): para um usuário leigo, "um arquivo que se clica" vale mais que os
  poucos segundos a mais de abertura do one-dir. Reavaliar para one-dir só se a abertura incomodar.
- **Sem console** (`console=False`): é um app gráfico; nada de janela preta de terminal.
- **O driver NI-DAQmx nativo fica FORA do bundle.** É gratuito da NI e instalado uma vez na máquina;
  o `.exe` embute só o **wrapper Python `nidaqmx`**. Documentado no guia de campo como pré-requisito.
- **`.spec` versionado em `packaging/ensaios-ni.spec`**, reprodutível — não o comando solto de
  `pyinstaller` com dez flags. Coleta defensiva dos submódulos de `pyqtgraph`/`nidaqmx`/`openpyxl`
  (carregam coisas dinamicamente que o PyInstaller não vê por análise estática).
- **`pyinstaller` é extra opcional `[build]`** no `pyproject` — não pesa no dev/teste do Mac.

## Consequências

**Melhora:**

- O tio recebe um **`.exe` clicável** — destrava a adoção (a Fase 6 existe para isto).
- Build reprodutível e versionado; o próximo agente/dev roda um comando só.

**Piora / pendente:**

- **Só se valida no Windows.** No Mac dá para preparar e revisar o `.spec`; gerar/testar o binário
  exige o Windows (e o Mac nem tem `nidaqmx` para a coleta). Não há teste automatizado do binário.
- **PySide6 + pyqtgraph no PyInstaller** costumam exigir ajuste de hidden imports/hooks; é esperado
  que o **primeiro build** no Windows precise de um ou dois ciclos de correção. O `.spec` já traz os
  hooks conhecidos para reduzir isso.
- **one-file** descompacta em pasta temporária a cada abertura → startup alguns segundos mais lento.
- Falta o passo seguinte da Fase 6 (não coberto aqui): **robustez de longa duração** (rotação de
  arquivo, queda de rede) e **mensagens de erro amigáveis** — ver [roadmap.md](../roadmap.md).
