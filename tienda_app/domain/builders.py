from decimal import Decimal

from .logic import CalculadorImpuestos
from ..models import Orden


class OrdenBuilder:
    """Construye una orden paso a paso y valida los datos requeridos."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._usuario = None
        self._libro = None
        self._cantidad = 1
        self._direccion = ""

    def con_usuario(self, usuario):
        self._usuario = usuario
        return self

    def con_libro(self, libro):
        self._libro = libro
        return self

    def con_cantidad(self, cantidad):
        if not isinstance(cantidad, int) or cantidad < 1:
            raise ValueError("La cantidad debe ser un entero mayor que cero.")
        self._cantidad = cantidad
        return self

    def para_envio(self, direccion):
        self._direccion = (direccion or "").strip()
        return self

    def build(self) -> Orden:
        if self._libro is None:
            raise ValueError("Datos insuficientes para crear la orden: falta el libro.")

        total_unitario = CalculadorImpuestos.obtener_total_con_iva(self._libro.precio)
        total = (Decimal(total_unitario) * self._cantidad).quantize(Decimal("0.01"))
        orden = Orden.objects.create(
            usuario=self._usuario,
            libro=self._libro,
            total=total,
            direccion_envio=self._direccion,
        )
        self.reset()
        return orden
