from decimal import Decimal


class CalculadorImpuestos:
    """Calcula el total con IVA sin depender de Django ni de infraestructura."""

    TASA_IVA = Decimal("1.19")

    @staticmethod
    def obtener_total_con_iva(precio_base):
        return (Decimal(str(precio_base)) * CalculadorImpuestos.TASA_IVA).quantize(
            Decimal("0.01")
        )
