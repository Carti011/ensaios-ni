# Guia de instalação no Windows (passo a passo simples)

Este guia é para um **humano** colocar o projeto pra funcionar num computador Windows —
seja o do Weslley (com dispositivos simulados) ou o do tio (com o hardware de verdade).
Não precisa saber programar. Siga na ordem.

> **O que este projeto já faz hoje:** ele lê sinais, converte para a unidade certa
> (kgf, bar, etc.) e grava num arquivo de planilha (CSV). A parte que conversa com o
> hardware da National Instruments **ainda está sendo construída** (é a próxima etapa,
> feita justamente no Windows). Então, por enquanto, no Windows dá pra **montar o
> ambiente e rodar os testes** — ler o hardware de verdade vem logo em seguida.

---

## Tem o Claude Code instalado? (caminho fácil)

Se você abriu este projeto com o Claude Code, **não precisa decorar comando nenhum.**
Cole esta frase para ele:

> "Faça o onboarding deste projeto no Windows seguindo o runbook do CLAUDE.md:
> confira o Python, instale com o extra de hardware, rode os testes e me diga o que falta."

Ele vai executar tudo e te avisar se faltar instalar o driver da NI. O resto deste guia
é o mesmo passo a passo, para quando **não** houver Claude Code (no computador do tio).

---

## Não tem Claude Code? (passo a passo manual)

### Passo 1 — Instalar o Python

1. Baixe o Python 3.12 (ou mais novo) em <https://www.python.org/downloads/>.
2. No instalador, **marque a caixinha "Add Python to PATH"** antes de clicar em instalar.
3. Para conferir, abra o **Prompt de Comando** (tecla Windows → digite `cmd`) e rode:

   ```text
   python --version
   ```

   Tem que aparecer algo como `Python 3.12.x`.

### Passo 2 — Instalar o driver da National Instruments

Só é necessário no computador que tem o hardware (ou os dispositivos simulados).

1. Baixe o **NI-DAQmx** (é gratuito) em <https://www.ni.com/pt-br/support/downloads/drivers/download.ni-daq-mx.html>.
2. Instale. Ele já traz junto o **NI-MAX**, o programa onde o chassi aparece.
3. Abra o **NI-MAX** e confirme que o chassi (cDAQ-9184) e os módulos aparecem na lista.

> No computador do Weslley, em vez do hardware real, criam-se **dispositivos simulados**
> dentro do NI-MAX (chassi e módulos "de mentira" que devolvem dados de teste).

### Passo 3 — Baixar o projeto

No Prompt de Comando, vá até a pasta onde quer guardar o projeto e rode:

```text
git clone <endereço-do-repositório>
cd ensaios-ni
```

(Se não tiver o `git`, baixe em <https://git-scm.com/download/win>.)

### Passo 4 — Instalar o projeto

Dentro da pasta `ensaios-ni`, rode:

```text
pip install -e .[hardware]
```

Isso instala o programa e a peça que fala com a NI (`nidaqmx`).

### Passo 5 — Conferir que está tudo certo

Rode os testes:

```text
pytest
```

Se aparecer algo como **"19 passed"** (ou mais), o projeto está saudável nesta máquina.

### Passo 6 — Configurar os canais (o mapa dos sensores)

Aqui é onde você diz ao programa **o que está ligado em cada entrada** e **como
transformar o sinal elétrico no número físico** (ex.: volts → kgf).

1. Na pasta `config/`, copie o arquivo `canais.exemplo.toml` e renomeie a cópia para
   `canais.toml`.
2. Abra o `canais.toml` no Bloco de Notas e preencha cada canal com:
   - o **nome real** do canal (esse nome aparece no NI-MAX, ex.: `cDAQ9184-1820306Mod1/ai0`);
   - a **unidade** final (kgf, bar, mm…);
   - os números da conversão (**ganho** e **offset**).
3. Salve. Esse arquivo fica só no seu computador — ele **não** é enviado para o repositório.

> Cada trabalho do tio (um prédio, uma roda, uma ponte…) é um **arquivo de config
> diferente**. O programa é o mesmo; muda só esse mapa de canais. Guarde uma cópia de
> cada `canais.toml` por trabalho, com um nome que lembre o ensaio.

---

## E se eu não souber preencher os números da conversão?

Esses números (ganho, offset, gage factor do extensômetro) vêm de **quem conhece os
sensores** — normalmente do datasheet de cada sensor ou de uma calibração. Não dá pra
inventar: sem eles o programa lê, mas o número não significa nada. Esse levantamento é
um passo à parte, fora da instalação. Enquanto isso, dá pra usar os valores de exemplo
só para testar que o fluxo funciona.

---

## Resumo de bolso

| Passo | Comando |
| ----- | ------- |
| Ver Python | `python --version` |
| Baixar projeto | `git clone <repo>` e `cd ensaios-ni` |
| Instalar | `pip install -e .[hardware]` |
| Testar | `pytest` |
| Configurar | copiar `config/canais.exemplo.toml` → `config/canais.toml` e preencher |

Detalhe técnico completo do hardware e da API: [contexto-hardware.md](contexto-hardware.md).
