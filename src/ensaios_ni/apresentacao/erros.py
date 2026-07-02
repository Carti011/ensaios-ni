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


def mensagem_de_erro_de_aquisicao(erro: BaseException) -> str:
    if _driver_ausente(erro):
        return (
            "O driver NI-DAQmx não está instalado nesta máquina. Baixe e instale o driver "
            "gratuito da National Instruments (ni.com) e abra o programa novamente."
        )
    if _erro_do_driver_ni(erro):
        return (
            "Não foi possível comunicar com o hardware NI. Confira no NI-MAX se o chassi "
            "aparece — ligado, cabo de rede conectado e IP correto — e se os canais do "
            f"arquivo de configuração existem no equipamento. (detalhe técnico: {erro})"
        )
    return f"Falha na aquisição: {erro}"
