from collections.abc import Callable
from pathlib import Path

from ensaios_ni.aquisicao.porta import FonteDeAquisicao
from ensaios_ni.dominio.canais import Canais
from ensaios_ni.dominio.conversao import calcular_tara, converter
from ensaios_ni.persistencia.csv_ensaio import GravadorEnsaioCsv, gravar_ensaio


def executar_ensaio(
    fonte: FonteDeAquisicao,
    canais: Canais,
    amostras: int,
    taxa_hz: float,
    caminho: Path,
    amostras_tara: int = 0,
) -> None:
    """Lê os canais configurados (tensão e/ou strain), converte e grava em CSV.

    Tensão (9205) e strain (9235) são lidos em tasks separadas (tipos de medição
    diferentes) e gravados juntos, na ordem em que aparecem no config. Se
    `amostras_tara > 0`, faz antes uma leitura de repouso e usa a média como tara
    (zero) de cada canal — o "Zero Channel" do fluxo do dono.
    """
    nomes = list(canais)
    taras = _capturar_taras(fonte, canais, nomes, amostras_tara, taxa_hz)
    leituras = _ler_por_tipo(fonte, canais, nomes, amostras, taxa_hz)
    valores_por_canal: dict[str, list[float]] = {}
    unidades: dict[str, str] = {}
    for nome in nomes:
        canal = canais[nome]
        valores_por_canal[nome] = [converter(v, canal, tara=taras[nome]) for v in leituras[nome]]
        unidades[nome] = canal.unidade
    gravar_ensaio(caminho, valores_por_canal, taxa_hz, unidades)


def executar_ensaio_continuo(
    fonte: FonteDeAquisicao,
    canais: Canais,
    taxa_hz: float,
    caminho: Path,
    amostras_por_bloco: int,
    amostras_tara: int = 0,
    duracao_s: float | None = None,
    parar: Callable[[], bool] | None = None,
) -> None:
    """Adquire em fluxo contínuo (blocos) e grava o CSV incrementalmente.

    Para monitoramento de longa duração (ADR-007): em vez de ler N amostras e
    parar, transmite blocos e os grava em append, sem acumular tudo em memória.
    Tensão e strain são lidos em fluxos separados, costurados bloco a bloco. Se
    `amostras_tara > 0`, captura a tara (zero) por canal antes de iniciar o fluxo.
    Se `duracao_s` for informado, encerra ao cobrir esse tempo (arredondado ao bloco).
    `parar` é um sinal opcional consultado a cada bloco (a CLI o liga ao Ctrl-C) para
    encerramento limpo de ensaios abertos — sempre gravando o bloco corrente antes de sair.
    """
    nomes = list(canais)
    unidades = {nome: canais[nome].unidade for nome in nomes}
    taras = _capturar_taras(fonte, canais, nomes, amostras_tara, taxa_hz)
    fluxos = _abrir_fluxos(fonte, canais, nomes, taxa_hz, amostras_por_bloco)
    alvo = None if duracao_s is None else round(duracao_s * taxa_hz)
    gravadas = 0
    with GravadorEnsaioCsv(caminho, nomes, taxa_hz, unidades) as gravador:
        for partes in zip(*fluxos):
            bloco: dict[str, list[float]] = {}
            for parte in partes:
                bloco.update(parte)
            convertido = {
                nome: [converter(v, canais[nome], tara=taras[nome]) for v in bloco[nome]]
                for nome in nomes
            }
            gravador.escrever_bloco(convertido)
            gravadas += len(bloco[nomes[0]])
            if alvo is not None and gravadas >= alvo:
                break
            if parar is not None and parar():
                break


def _abrir_fluxos(fonte, canais, nomes, taxa_hz, amostras_por_bloco):
    """Abre um fluxo (generator de blocos) por tipo de canal presente."""
    tensao = [nome for nome in nomes if canais[nome].tipo == "tensao"]
    strain = [nome for nome in nomes if canais[nome].tipo == "strain"]
    fluxos = []
    if tensao:
        fluxos.append(fonte.transmitir_tensao(tensao, taxa_hz, amostras_por_bloco))
    if strain:
        fluxos.append(fonte.transmitir_strain(strain, taxa_hz, amostras_por_bloco))
    return fluxos


def _ler_por_tipo(
    fonte: FonteDeAquisicao,
    canais: Canais,
    nomes: list[str],
    amostras: int,
    taxa_hz: float,
) -> dict[str, list[float]]:
    """Particiona os canais por tipo e lê cada grupo na sua task, combinando o resultado."""
    tensao = [nome for nome in nomes if canais[nome].tipo == "tensao"]
    strain = [nome for nome in nomes if canais[nome].tipo == "strain"]
    leituras: dict[str, list[float]] = {}
    if tensao:
        leituras.update(fonte.ler_tensao(tensao, amostras, taxa_hz))
    if strain:
        leituras.update(fonte.ler_strain(strain, amostras, taxa_hz))
    return leituras


def _capturar_taras(
    fonte: FonteDeAquisicao,
    canais: Canais,
    nomes: list[str],
    amostras_tara: int,
    taxa_hz: float,
) -> dict[str, float]:
    if amostras_tara <= 0:
        return {nome: 0.0 for nome in nomes}
    repouso = _ler_por_tipo(fonte, canais, nomes, amostras_tara, taxa_hz)
    return {nome: calcular_tara(repouso[nome], canais[nome]) for nome in nomes}
