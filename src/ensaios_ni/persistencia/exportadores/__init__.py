from ensaios_ni.persistencia.exportadores.csv_excel_br import exportar_csv_excel_br
from ensaios_ni.persistencia.exportadores.xlsx import exportar_xlsx

# Registro plugável formato -> rotina; a CLI seleciona por nome sem conhecer cada exportador.
EXPORTADORES = {
    "csv-excel-br": exportar_csv_excel_br,
    "xlsx": exportar_xlsx,
}

__all__ = ["exportar_csv_excel_br", "exportar_xlsx", "EXPORTADORES"]
