def formatar_moeda(valor):
    # 1,234.56 -> 1.234,56
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")

    return f"R$ {texto}"
