# Contexto de hardware — ensaios-ni

Documento fonte-da-verdade do hardware. Objetivo do projeto: substituir LabVIEW/FlexLogger (pagos) por um software próprio em Python que lê os sensores conectados ao chassi NI e registra/apresenta os dados dos ensaios. O driver que acessa o hardware (NI-DAQmx) é gratuito; o que se elimina é a camada de aplicação paga.

> A **API do `nidaqmx` na §4 está pinada contra a doc oficial.** Não inventar assinaturas — usar exatamente os métodos abaixo. Esta é a parte que um agente sem o `nidaqmx` no treino mais alucina.

---

## 1. Hardware confirmado (lido das etiquetas físicas)

**Chassi**

- **NI cDAQ-9184** — CompactDAQ de 4 slots, conexão **Gigabit Ethernet** (RJ45). P/N 152778B-01L, fabricado na Hungria. O MAC usa o OUI `00:80:2F` (prefixo público da National Instruments). Faixa de operação -20 a +55 °C. O chassi não mede nada sozinho: fornece timing, conexão e alimentação aos módulos. _(S/N e MAC completo omitidos — repo público; ficam só no cofre privado.)_

**Módulos (C Series)**

- **2× NI 9205** — entrada analógica de **tensão**. 32 canais single-ended / 16 diferenciais, faixa de ±200 mV a ±10 V, 16 bits, 250 kS/s agregado. Terminais ACH0–ACH31 + COM. Cadeia interna: MUX → PGIA → ADC isolado de 16 bits.
- **1× NI 9235** — entrada de **strain gauge (extensometria)**. 8 canais, quarter-bridge, completação de **120 Ω embutida**, 24 bits, **excitação interna fixa de 2,0 V** (confirmado no diagrama da etiqueta). Terminais por canal: EXC / AI / RC.

> Os slots físicos de cada módulo só são confirmados abrindo o NI-MAX. Os nomes reais dos dispositivos (ex.: `cDAQ9184-1820306Mod1`) vêm de lá.

---

## 2. Restrições que definem toda a arquitetura

1. **NI-DAQmx roda só em Windows e Linux x86.** Não existe versão para macOS nem para ARM. A camada de aquisição **tem que executar em Windows** (ou Linux x86). O MacBook M4 serve só para escrever código e rodar os testes do domínio/fake — nunca para acessar hardware ou dispositivo simulado.
2. **Dá para desenvolver e testar sem o hardware presente.** Duas vias, não confundir:
   - **Adaptador fake (Mac):** dados sintéticos em Python puro, sem NI-DAQmx. É o loop de TDD.
   - **Dispositivo simulado (NI-MAX, Windows):** chassi/módulos virtuais do driver; valida o adaptador real sem o hardware. Não é teste unitário.
3. **NI-MAX continua em uso** (gratuito) — é onde o chassi é descoberto/reservado e onde se confirmam os nomes dos dispositivos. O que some é o FlexLogger/LabVIEW.

### Fluxo de trabalho (3 ambientes)

- **MacBook (Claude Code):** escrever código, versionar, subir no GitHub, rodar testes de domínio/fake.
- **Windows do desenvolvedor:** `git clone`, rodar com **dispositivos simulados** no NI-MAX. Valida tasks, leitura, conversão, persistência, dashboard — sem o hardware.
- **Windows do dono do hardware:** `git clone`, trocar os nomes simulados pelos reais, validar contra o sinal físico e calibrar a extensometria.

---

## 3. Conceitos do NI-DAQmx que a arquitetura precisa respeitar

- Unidade central = **Task**: conjunto de canais + configuração de timing + trigger. Cria, configura, lê, fecha.
- **Tensão e strain são tipos diferentes → tasks separadas.** Não misturar `add_ai_voltage_chan` com `add_ai_strain_gage_chan` na mesma task.
- Os **dois 9205 podem compartilhar uma única task** (mesmo tipo de medição, mesmo chassi, mesmo sample clock). O **9235 fica em task própria**.
- Se os ensaios exigem todos os canais alinhados no tempo, sincroniza-se as duas tasks compartilhando o sample clock / start trigger do chassi. Para o MVP, rodar uma de cada vez já basta.
- **No cDAQ-9184 (Ethernet), o 9235 (delta-sigma) exige `cfg_samp_clk_timing` explícito — leitura on-demand (`task.read()` sem timing) falha.** Os 9205 toleraram on-demand no mesmo chassi, mas ambas as tasks devem configurar sample clock por consistência. _Descoberto na validação com dispositivos simulados no NI-MAX (22/06/2026)._

---

## 4. API real do nidaqmx (usar estes métodos — não inventar assinaturas)

Instalação no Windows: driver NI-DAQmx (gratuito, ni.com) + `pip install nidaqmx` (Python 3.9+).

**Listar dispositivos (confirma se NI-MAX enxerga tudo):**

```python
import nidaqmx
sistema = nidaqmx.system.System.local()
print([d.name for d in sistema.devices])
```

**Leitura de tensão (9205):**

```python
import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan(
        "Mod1/ai0",
        terminal_config=TerminalConfiguration.DIFF,  # ou RSE, conforme a fiação física
        min_val=-10.0, max_val=10.0,
    )
    task.timing.cfg_samp_clk_timing(
        rate=1000,
        sample_mode=AcquisitionType.CONTINUOUS,
    )
    dados = task.read(number_of_samples_per_channel=100)
```

**Leitura de strain (9235) — assinatura real e os defaults que PRECISAM ser trocados:**

Assinatura oficial do método (defaults entre parênteses):
`add_ai_strain_gage_chan(physical_channel, name_to_assign_to_channel='', min_val=-0.001, max_val=0.001, units=StrainUnits.STRAIN, strain_config=StrainGageBridgeType.FULL_BRIDGE_I, voltage_excit_source=ExcitationSource.INTERNAL, voltage_excit_val=2.5, gage_factor=2.0, initial_bridge_voltage=0.0, nominal_gage_resistance=350.0, poisson_ratio=0.3, lead_wire_resistance=0.0, custom_scale_name='')`

```python
import nidaqmx
from nidaqmx.constants import StrainGageBridgeType, ExcitationSource, StrainUnits

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_strain_gage_chan(
        "Mod2/ai0",
        strain_config=StrainGageBridgeType.QUARTER_BRIDGE_I,  # default é FULL_BRIDGE — OBRIGATÓRIO trocar
        voltage_excit_source=ExcitationSource.INTERNAL,
        voltage_excit_val=2.0,            # 9235 tem excitação interna fixa de 2,0 V (default da API é 2,5)
        nominal_gage_resistance=120.0,    # 9235 é 120 Ω (default da API é 350)
        gage_factor=2.0,                  # CONFIRMAR no datasheet do extensômetro usado
        poisson_ratio=0.3,                # CONFIRMAR conforme o material
        initial_bridge_voltage=0.0,       # vem do "zero"/nulling com a peça em repouso
        units=StrainUnits.STRAIN,
        min_val=-0.001, max_val=0.001,    # faixa de deformação esperada
    )
    task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.CONTINUOUS)
    deformacao = task.read(number_of_samples_per_channel=100)
```

> **ARMADILHA PRINCIPAL DO PROJETO:** os defaults de `add_ai_strain_gage_chan` são para full-bridge 350 Ω 2,5 V. Rodando sem trocar para quarter-bridge 120 Ω 2,0 V, os valores saem **plausíveis mas errados, sem lançar nenhum erro**. Sempre validar contra o test panel do NI-MAX.

**Aquisição contínua de verdade** (em vez de `read` pontual): registrar callback de buffer
`task.register_every_n_samples_acquired_into_buffer_event(N, callback)`
ou usar `nidaqmx.stream_readers.AnalogMultiChannelReader` para throughput maior.

---

## 5. Arquitetura de software

Decisão registrada em [adr/001-arquitetura-porta-adaptador.md](adr/001-arquitetura-porta-adaptador.md). Camadas:

- **Aquisição (porta + adaptadores):** a porta `FonteDeAquisicao` é a única interface que o resto conhece. Adaptador `daqmx` (real, Windows, único que importa `nidaqmx`) e `fake` (sintético, Mac). É a única parte amarrada a Windows/DAQmx.
- **Domínio / conversão:** volts → unidade física (kgf, bar, °C, mm…) por canal, parametrizado por **config** (`config/canais.toml`). **Essa informação vem do dono do hardware, não do equipamento.**
- **Persistência:** começar em CSV (ou TDMS, formato binário nativo da NI, bom para alta taxa). PostgreSQL depois, se precisar de histórico consultável.
- **Apresentação (dashboard):** Fase 4 — stack decidida no [ADR-013](adr/013-stack-do-dashboard.md) (PyQt6/pyqtgraph). A aquisição nunca vai para o navegador — fica no backend Windows.

**Ordem de execução (regra de ouro):** provar a leitura de **um** canal real → CSV **antes** de construir qualquer dashboard. Interface bonita exibindo volts sem significado é o erro mais comum nesse tipo de projeto.

---

## 6. Levantamento com o dono do hardware (majoritariamente respondido)

> Detalhe completo, transcrições e o que ainda falta (rodada 3) em [respostas-tio.md](respostas-tio.md).
> Resumo do que ficou definido (rodada 2, 22/06/2026):

**9235 (strain):** quarter-bridge **120 Ω**; **gage factor 2,14–2,16** (varia por lote →
configurável); cabo longo usa **3 fios, 22 AWG** (compensação de lead wire); nº de canais varia
por obra. Saída em **microstrain** (×1.000.000), com **null/tara** no início.

**9205 (tensão):** **LVDT** (deslocamento) e **acelerômetro** (alimentado por **5 V externos**,
pois a placa não excita); também pressão (MPa) e carga (kgf). Célula de carga: liga via
condicionador com **saída em tensão** (não ponte crua). **Fiação: diferencial** (confirmado pelo
dono, 23/06). **Acelerômetro: Dytran 7523A1** (triaxial DC-response/capacitivo) — **550 mV/g, ±2g,
0–1500 Hz, 5 V DC**; vira canal de tensão com ganho ≈ 1,818 g/V.

**Conversão:** **não é fórmula fixa** — é **calibração empírica por pontos + tara**, como no
AqDados/Lynx. Ver [ADR-006](adr/006-calibracao-por-pontos.md).

**Ensaio:** vibração com **acelerômetro 2G a 1024 Hz**; carga × deformação a taxa baixa (não
quantificada). Duração de **1 h a 1 ano contínuo** → exige aquisição contínua
([ADR-007](adr/007-aquisicao-continua.md)).

**Rede:** chassi **direto no PC, IP fixo** (número no cofre privado, fora do repo).

**Ainda em aberto (rodada 3):** fiação do 9205, célula de carga, sensibilidades/faixas dos
sensores, taxa dos ensaios lentos, formato de arquivo para compatibilidade com AqDados/AqDAnalysis.

---

## 7. Estratégia de validação

- Antes de escrever Python, usar o **test panel do NI-MAX** para confirmar leitura coerente de um canal — prova que hardware + rede estão ok, sem código no meio.
- Comparar os valores do software com os do test panel do NI-MAX no mesmo canal. Se baterem, a configuração da task está correta. **Esse é o critério objetivo de "funcionou".**

---

## 8. Plano em fases

> **Fonte única do plano e do status: [roadmap.md](roadmap.md).** Não duplicar a lista de fases
> aqui — esta seção guarda só as notas técnicas das fases de ambiente que não cabem no roadmap.

Resumo do estado (detalhe e fases 0–6 no roadmap): **Fases 0–4 concluídas** — ambiente, prova de
vida, aquisição (tensão + strain, finito + contínuo), conversão/exportação (todo o backend) e o
**dashboard** (PySide6/pyqtgraph). Faltam a **5** (validação física no hardware) e a **6**
(empacotamento & adoção).

**Notas técnicas das fases 0–1 (validadas no Windows simulado, 22/06/2026):** dispositivos
simulados `cDAQ1` + `cDAQ1Mod1`/`Mod2` (9205) + `cDAQ1Mod3` (9235); Python enxerga todos via
`nidaqmx` e leu 9205 e 9235 sem erro. _Os nomes são do simulado; no hardware real serão outros
(ex.: `cDAQ9184-1820306Mod1`)._ A descoberta do **sample clock explícito** obrigatório no 9235
(delta-sigma no chassi Ethernet) está no §3.

---

## Anexo — proveniência

Hardware identificado a partir das etiquetas físicas fotografadas (cDAQ-9184; 2× 9205; 1× 9235) e do relato em áudio do dono do equipamento. A descrição do áudio bate com as etiquetas. As infos da §6 ainda não foram levantadas com ele — são o próximo passo fora do código.
