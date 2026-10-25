def formatar_moeda(valor):
    # 1,234.56 -> 1.234,56
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")

    return f"R$ {texto}"


def formatar_data(data):
    if data is None:
        return "não registrada"

    return data.strftime("%d/%m/%Y %H:%M:%S")
