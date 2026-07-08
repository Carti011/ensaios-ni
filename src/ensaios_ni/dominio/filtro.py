"""Filtros de sinal para visualização ao vivo (o "filtro de ruído" do tio).

Puro e sem dependência externa: opera sobre a série já convertida, só para o
operador enxergar o sinal sem o ruído de alta frequência. **Não** entra na
gravação do CSV — o laudo guarda o dado cru (rastreabilidade). Espelha o "Filtro
Passa Banda" do AqDados / a "Filtragem" do AqDAnalysis.
"""


def media_movel(serie: list[float], janela: int) -> list[float]:
    """Suaviza a série pela média móvel centrada de `janela` pontos.

    Mantém o tamanho da série (bordas usam os pontos disponíveis), preservando o
    alinhamento com o eixo de tempo. `janela <= 1` devolve a série sem alteração.
    """
    if janela <= 1:
        return list(serie)
    raio = janela // 2
    n = len(serie)
    suave = []
    for i in range(n):
        ini = max(0, i - raio)
        fim = min(n, i + raio + 1)
        trecho = serie[ini:fim]
        suave.append(sum(trecho) / len(trecho))
    return suave
