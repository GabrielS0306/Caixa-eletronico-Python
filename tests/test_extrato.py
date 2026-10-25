import unittest

from datetime import date, datetime
from decimal import Decimal

from caixa_eletronico.nucleo.conta_bancaria import TipoTransacao, Transacao
from caixa_eletronico.nucleo.extrato import (
    PeriodoInvalidoError,
    filtrar_por_periodo
)

def transacao(data):
    return Transacao(
        TipoTransacao.DEPOSITO, Decimal("10.00"), Decimal("10.00"), data
    )

class TestFiltrarPorPeriodo(unittest.TestCase):
    def setUp(self):
        self.sem_data = transacao(None)
        self.dia_01 = transacao(datetime(2026, 10, 1, 8, 0))
        self.dia_15 = transacao(datetime(2026, 10, 15, 12, 0))
        self.dia_31 = transacao(datetime(2026, 10, 31, 23, 59, 59))

        self.transacoes = (
            self.sem_data, self.dia_01, self.dia_15, self.dia_31
        )

    def test_sem_limites_traz_tudo(self):
        resultado = filtrar_por_periodo(self.transacoes)

        self.assertEqual(resultado, list(self.transacoes))

    def test_periodo_inclui_os_dias_limite(self):
        resultado = filtrar_por_periodo(
            self.transacoes, date(2026, 10, 1), date(2026, 10, 31)
        )

        self.assertEqual(resultado, [self.dia_01, self.dia_15, self.dia_31])

    def test_apenas_data_inicial(self):
        resultado = filtrar_por_periodo(
            self.transacoes, inicio=date(2026, 10, 15)
        )

        self.assertEqual(resultado, [self.dia_15, self.dia_31])

    def test_apenas_data_final(self):
        resultado = filtrar_por_periodo(
            self.transacoes, fim=date(2026, 10, 14)
        )

        self.assertEqual(resultado, [self.dia_01])

    def test_um_unico_dia(self):
        dia = date(2026, 10, 15)

        resultado = filtrar_por_periodo(self.transacoes, dia, dia)

        self.assertEqual(resultado, [self.dia_15])

    def test_periodo_sem_transacoes(self):
        resultado = filtrar_por_periodo(
            self.transacoes, date(2026, 11, 1), date(2026, 11, 30)
        )

        self.assertEqual(resultado, [])

    def test_data_inicial_depois_da_final(self):
        with self.assertRaises(PeriodoInvalidoError):
            filtrar_por_periodo(
                self.transacoes, date(2026, 10, 31), date(2026, 10, 1)
            )

if __name__ == "__main__":
    unittest.main()
