# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

## [Não lançado]

### Adicionado

- Estrutura do pacote Python (`pyproject.toml`, Python 3.12, `pytest`); `nidaqmx` como extra opcional `[hardware]`, não instalado no Mac.
- Porta `FonteDeAquisicao` (interface) com `ler_tensao`.
- Adaptador `fake` (dados sintéticos, Python puro) com leitura validada (canal inexistente, amostras demais e amostras não positivas falham claro).
- Domínio de conversão linear volts→unidade de engenharia (`ganho * volts + offset`), parametrizado por `config/canais.toml`.
- Carregamento e validação de `config/canais.toml` com erros de domínio (`CanalNaoConfigurado`, `ConfiguracaoInvalida`).
- Teste-guarda de arquitetura: falha se algum arquivo fora de `daqmx.py` importar `nidaqmx` (via AST).
- `config/canais.exemplo.toml` documentando o formato de configuração.
- ADR-002 — conversão linear por canal e contrato da porta retornando volts brutos.
