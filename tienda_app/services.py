from django.db import transaction
from django.shortcuts import get_object_or_404

from .domain.builders import OrdenBuilder
from .domain.logic import CalculadorImpuestos
from .models import Inventario, Libro


class CompraService:
    """Coordina la compra sin acoplarse a un proveedor de pagos concreto."""

    def __init__(self, procesador_pago):
        self.procesador_pago = procesador_pago
        self.builder = OrdenBuilder()

    def obtener_detalle_producto(self, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        inventario = Inventario.objects.filter(libro=libro).first()
        return {"libro": libro, "total": total, "stock": inventario.cantidad if inventario else 0}

    @transaction.atomic
    def ejecutar_compra(self, libro_id, cantidad=1, direccion="", usuario=None):
        if not isinstance(cantidad, int) or cantidad < 1:
            raise ValueError("La cantidad debe ser un entero mayor que cero.")

        libro = get_object_or_404(Libro, id=libro_id)
        inventario = get_object_or_404(Inventario.objects.select_for_update(), libro=libro)
        if inventario.cantidad < cantidad:
            raise ValueError("No hay suficiente stock para completar la compra.")

        orden = (
            self.builder.con_usuario(usuario)
            .con_libro(libro)
            .con_cantidad(cantidad)
            .para_envio(direccion)
            .build()
        )

        if not self.procesador_pago.pagar(orden.total):
            orden.delete()
            raise ValueError("La transacción fue rechazada por el procesador de pagos.")

        inventario.cantidad -= cantidad
        inventario.save(update_fields=["cantidad"])
        return orden.total
