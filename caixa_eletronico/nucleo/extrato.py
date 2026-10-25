class PeriodoInvalidoError(ValueError):
    """Data inicial posterior à data final."""


def filtrar_por_periodo(transacoes, inicio=None, fim=None):
    # Sem limites, o extrato traz tudo, inclusive transações antigas sem data
    if inicio is None and fim is None:
        return list(transacoes)

    if inicio is not None and fim is not None and inicio > fim:
        raise PeriodoInvalidoError(
            "A data inicial deve ser anterior ou igual à data final."
        )

    resultado = []

    for item in transacoes:
        # Sem data não dá para saber se a transação está no período
        if item.data is None:
            continue

        dia = item.data.date()

        if inicio is not None and dia < inicio:
            continue

        if fim is not None and dia > fim:
            continue

        resultado.append(item)

    return resultado
