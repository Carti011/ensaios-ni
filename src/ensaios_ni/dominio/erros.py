class ErroDeDominio(Exception):
    """Base dos erros de domínio."""


class CanalNaoConfigurado(ErroDeDominio):
    def __init__(self, nome: str):
        super().__init__(f"canal '{nome}' não está configurado em canais.toml")
        self.nome = nome


class ConfiguracaoInvalida(ErroDeDominio):
    """Config de canais malformada (campo faltando ou valor inválido)."""
