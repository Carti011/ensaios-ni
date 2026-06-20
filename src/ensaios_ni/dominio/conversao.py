from ensaios_ni.dominio.canais import Canal


def converter(volts: float, canal: Canal) -> float:
    """Converte tensão crua em unidade de engenharia: ganho * volts + offset."""
    return canal.ganho * volts + canal.offset
