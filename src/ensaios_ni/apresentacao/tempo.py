"""Parse e formatação de tempo para a UI de exportação (Fase 4 — ADR-012).

Puro (testável no Mac): traduz o tempo do ensaio entre segundos (o que o CSV usa) e formas
amigáveis para o tio — `hh:mm:ss` / `dd:hh:mm:ss` na entrada e duração legível na exibição.
"""


def parsear_tempo(texto: str) -> float | None:
    """Converte o texto de um campo de janela em segundos, ou None (sem limite = ensaio inteiro).

    Aceita segundos ("93600", "90,5"), `hh:mm:ss` ("26:00:00") ou `dd:hh:mm:ss` ("1:02:00:00").
    Vazio ou inválido vira None de propósito: o campo é opcional e não pode quebrar a exportação.
    """
    texto = texto.strip().replace(",", ".")
    if not texto:
        return None
    if ":" in texto:
        return _parsear_relogio(texto)
    try:
        return float(texto)
    except ValueError:
        return None


def _parsear_relogio(texto: str) -> float | None:
    partes = texto.split(":")
    if len(partes) not in (3, 4):  # hh:mm:ss ou dd:hh:mm:ss
        return None
    try:
        valores = [float(parte) for parte in partes]
    except ValueError:
        return None
    dias = valores[0] if len(valores) == 4 else 0.0
    horas, minutos, segundos = valores[-3:]
    return dias * 86400 + horas * 3600 + minutos * 60 + segundos


def formatar_duracao(segundos: float) -> str:
    """Duração legível ("2 d 2 h 55 min"), omitindo os componentes zerados (0 = "0 s")."""
    total = int(segundos)
    dias, resto = divmod(total, 86400)
    horas, resto = divmod(resto, 3600)
    minutos, segs = divmod(resto, 60)
    partes = [
        (dias, "d"),
        (horas, "h"),
        (minutos, "min"),
        (segs, "s"),
    ]
    nao_zero = [f"{valor} {rotulo}" for valor, rotulo in partes if valor]
    return " ".join(nao_zero) if nao_zero else "0 s"
