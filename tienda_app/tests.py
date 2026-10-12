import os
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .domain.builders import OrdenBuilder
from .domain.logic import CalculadorImpuestos
from .infra.factories import BancoNacionalProcesador, MockPaymentProcessor, PaymentFactory
from .models import Inventario, Libro, Orden
from .services import CompraService


class PaymentFactoryTests(TestCase):
    def test_factory_uses_mock_from_environment(self):
        with patch.dict(os.environ, {"PAYMENT_PROVIDER": "MOCK"}):
            self.assertIsInstance(PaymentFactory.get_processor(), MockPaymentProcessor)

    def test_factory_defaults_to_bank_processor(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsInstance(PaymentFactory.get_processor(), BancoNacionalProcesador)


class OrdenBuilderTests(TestCase):
    def setUp(self):
        self.libro = Libro.objects.create(titulo="Arquitectura Limpia", precio=Decimal("100.00"))

    def test_builder_creates_order_with_iva_and_shipping_data(self):
        orden = (
            OrdenBuilder().con_libro(self.libro).con_cantidad(2)
            .para_envio("Calle 123").build()
        )
        self.assertEqual(orden.total, Decimal("238.00"))
        self.assertEqual(orden.direccion_envio, "Calle 123")

    def test_builder_requires_a_book(self):
        with self.assertRaisesMessage(ValueError, "falta el libro"):
            OrdenBuilder().build()


class CompraServiceTests(TestCase):
    def setUp(self):
        self.libro = Libro.objects.create(titulo="Patrones de diseño", precio=Decimal("100.00"))
        self.inventario = Inventario.objects.create(libro=self.libro, cantidad=3)

    def test_successful_purchase_reduces_stock(self):
        class PagoAprobado:
            def pagar(self, monto):
                return True

        servicio = CompraService(PagoAprobado())
        total = servicio.ejecutar_compra(self.libro.id, cantidad=2, direccion="Carrera 1")
        self.inventario.refresh_from_db()
        self.assertEqual(total, Decimal("238.00"))
        self.assertEqual(self.inventario.cantidad, 1)
        self.assertEqual(Orden.objects.count(), 1)

    def test_purchase_rejects_insufficient_stock(self):
        servicio = CompraService(MockPaymentProcessor())
        with self.assertRaisesMessage(ValueError, "No hay suficiente stock"):
            servicio.ejecutar_compra(self.libro.id, cantidad=4)
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.cantidad, 3)
        self.assertEqual(Orden.objects.count(), 0)

    def test_tax_calculation_uses_decimal(self):
        self.assertEqual(CalculadorImpuestos.obtener_total_con_iva("100"), Decimal("119.00"))

class CompraAPITests(TestCase):
    """Pruebas del endpoint DRF sin tocar la base de datos real."""

    def setUp(self):
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.libro = Libro.objects.create(
            titulo="Libro de prueba API",
            precio=Decimal("100.00"),
        )
        self.inventario = Inventario.objects.create(libro=self.libro, cantidad=3)

    def test_post_compra_crea_orden_y_descuenta_inventario(self):
        class PagoAprobado:
            def pagar(self, monto):
                return True

        with patch("tienda_app.api.views.PaymentFactory.get_processor", return_value=PagoAprobado()):
            response = self.client.post(
                "/api/v1/comprar/",
                {
                    "libro_id": self.libro.id,
                    "direccion_envio": "Carrera 10 # 20-30",
                    "cantidad": 2,
                },
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["estado"], "exito")
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.cantidad, 1)
        self.assertEqual(Orden.objects.filter(libro=self.libro).count(), 1)

    def test_post_compra_datos_invalidos_devuelve_400(self):
        response = self.client.post(
            "/api/v1/comprar/",
            {"libro_id": "no-es-un-id", "direccion_envio": "Calle 1"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.cantidad, 3)
        self.assertEqual(Orden.objects.filter(libro=self.libro).count(), 0)

    def test_post_compra_sin_stock_devuelve_409(self):
        class PagoAprobado:
            def pagar(self, monto):
                return True

        with patch("tienda_app.api.views.PaymentFactory.get_processor", return_value=PagoAprobado()):
            response = self.client.post(
                "/api/v1/comprar/",
                {
                    "libro_id": self.libro.id,
                    "direccion_envio": "Calle 1",
                    "cantidad": 4,
                },
                format="json",
            )

        self.assertEqual(response.status_code, 409)
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.cantidad, 3)
        self.assertEqual(Orden.objects.filter(libro=self.libro).count(), 0)

