from pathlib import Path

from ensaios_ni.aplicacao.demo import executar_demonstracao


def main() -> None:
    saida = Path("ensaio-demo.csv")
    executar_demonstracao(saida)
    print(f"Ensaio de demonstração gravado em: {saida.resolve()}")


if __name__ == "__main__":
    main()
