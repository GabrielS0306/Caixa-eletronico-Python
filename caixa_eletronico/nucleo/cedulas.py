from caixa_eletronico.formatacao import formatar_moeda

# Para este conjunto de cédulas, escolher sempre a maior possível (algoritmo
# guloso) já resulta no menor número de notas. Isso não vale para qualquer
# conjunto: com notas de 5 e 2, por exemplo, 8 = 2+2+2+2, mas o guloso tentaria 5.
CEDULAS = (200, 100, 50, 20, 10)


class CedulasIndisponiveisError(ValueError):
    """Valor que não pode ser pago com as cédulas do caixa."""


def calcular_cedulas(valor):
    restante = valor
    entregues = {}

    for cedula in CEDULAS:
        quantidade, restante = divmod(restante, cedula)

        if quantidade:
            entregues[cedula] = int(quantidade)

    if restante:
        raise CedulasIndisponiveisError(
            "Valor indisponível! Digite um valor múltiplo de "
            f"{formatar_moeda(min(CEDULAS))}."
        )

    return entregues
