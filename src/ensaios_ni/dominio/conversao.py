from ensaios_ni.dominio.canais import Canal


def converter(volts: float, canal: Canal, tara: float = 0.0) -> float:
    """Converte tensão crua em unidade de engenharia (escala por pontos ou linear), menos a tara."""
    if canal.pontos is not None:
        escalado = _interpolar(volts, canal.pontos)
    else:
        escalado = canal.ganho * volts + canal.offset
    return escalado - tara


def calcular_tara(amostras: list[float], canal: Canal) -> float:
    """Tara (zero) na unidade de engenharia: média do repouso convertido, à la 'Zero Channel'."""
    convertidas = [converter(v, canal) for v in amostras]
    return sum(convertidas) / len(convertidas)


def _interpolar(volts: float, pontos: tuple[tuple[float, float], ...]) -> float:
    # clamp fora da faixa (como o DAQmx faz na leitura por tabela)
    if volts <= pontos[0][0]:
        return pontos[0][1]
    if volts >= pontos[-1][0]:
        return pontos[-1][1]
    # interpolação linear no segmento que contém volts
    for (x0, y0), (x1, y1) in zip(pontos, pontos[1:]):
        if x0 <= volts <= x1:
            return y0 + (y1 - y0) * (volts - x0) / (x1 - x0)
