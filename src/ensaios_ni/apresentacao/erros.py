"""Tradução de erros crus da aquisição para mensagens que o operador entenda.

Módulo puro (sem PySide nem nidaqmx): o Presenter chama a tradução e o widget só
exibe o texto. Não importa `nidaqmx` — os erros do driver são reconhecidos pelo
módulo de origem da exceção (`type(erro).__module__`), não pelo tipo.
"""


def _driver_ausente(erro: BaseException) -> bool:
    return isinstance(erro, ImportError) and "nidaqmx" in (getattr(erro, "name", "") or str(erro))


def _erro_do_driver_ni(erro: BaseException) -> bool:
    # DaqError vem do módulo nidaqmx.errors; reconhecemos pela origem, sem importar nidaqmx
    return type(erro).__module__.split(".")[0] == "nidaqmx"


# heurísticas sobre o texto do DAQmx (inglês): fundadas na doc da NI, a confirmar no Windows.
# Se nenhuma casar, cai na mensagem genérica do driver — que já cobre chassi e canais.
_SINAIS_CHASSI = (
    "cannot be found",
    "cannot be accessed",
    "no longer present",
    "unable to communicate",
    "not connected",
    "reserved",
)


def _mensagem_do_driver_ni(erro: BaseException) -> str:
    texto = str(erro).lower()
    detalhe = f"(detalhe técnico: {erro})"
    if "physical channel" in texto:
        return (
            "Um canal do arquivo de configuração não existe no equipamento. Confira no NI-MAX "
            f"os nomes exatos dos canais e ajuste o canais.toml. {detalhe}"
        )
    if any(sinal in texto for sinal in _SINAIS_CHASSI):
        return (
            "O equipamento NI não foi encontrado. Confira se o chassi está ligado, com o cabo "
            f"de rede conectado e o IP correto — ele precisa aparecer no NI-MAX. {detalhe}"
        )
    return (
        "Não foi possível comunicar com o hardware NI. Confira no NI-MAX se o chassi aparece "
        "— ligado, cabo de rede conectado e IP correto — e se os canais do arquivo de "
        f"configuração existem no equipamento. {detalhe}"
    )


def mensagem_de_erro_de_aquisicao(erro: BaseException) -> str:
    if _driver_ausente(erro):
        return (
            "O driver NI-DAQmx não está instalado nesta máquina. Baixe e instale o driver "
            "gratuito da National Instruments (ni.com) e abra o programa novamente."
        )
    if _erro_do_driver_ni(erro):
        return _mensagem_do_driver_ni(erro)
    return f"Falha na aquisição: {erro}"
