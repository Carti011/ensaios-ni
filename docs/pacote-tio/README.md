# Pacote para o tio — tudo num lugar só

Esta pasta reúne **tudo o que você precisa para gerar o `.exe` e montar o `.zip`** que vai para o tio.
Abra por aqui e siga o [instrucoes-weslley.md](instrucoes-weslley.md).

## O que tem aqui

| Arquivo | Para quem | O que é |
| ------- | --------- | ------- |
| [instrucoes-weslley.md](instrucoes-weslley.md) | **você** | passo a passo: gerar o `.exe` no Windows, testar no simulado, montar a pasta no Desktop e zipar. **Não vai no zip.** |
| [LEIA.txt](LEIA.txt) | **o tio** | instruções simples de como abrir e usar o programa. **Vai no zip.** |
| [canais-exemplo.toml](canais-exemplo.toml) | modelo | base do `canais.toml`: copie, renomeie para `canais.toml`, preencha e inclua no zip. **Vai no zip (renomeado/preenchido).** |

## Resumo do fluxo (detalhe no [instrucoes-weslley.md](instrucoes-weslley.md))

1. **No Windows:** `pyinstaller packaging/ensaios-ni.spec` → gera `dist\ensaios-ni.exe`.
2. **(Recomendado)** testar o **Iniciar** no `.exe` com dispositivo simulado do NI-MAX.
3. **Montar uma pasta no Desktop** (ex.: `ensaios-ni-tio`) com **três** arquivos:
   - `ensaios-ni.exe` (do `dist\`)
   - `canais.toml` (copiado do `canais-exemplo.toml` e preenchido)
   - `LEIA.txt` (daqui)
4. **Zipar** a pasta e enviar. O tio descompacta e dá duplo-clique no `.exe`.

> O que **vai no zip**: os 3 de cima. O `instrucoes-weslley.md` e este `README.md` são só seus — não
> entram no pacote do tio.
