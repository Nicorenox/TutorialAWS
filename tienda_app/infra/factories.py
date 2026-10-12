import os

from .gateways import BancoNacionalProcesador


class MockPaymentProcessor:
    """Procesador de pago simulado para desarrollo y pruebas."""

    def pagar(self, monto) -> bool:
        print(f"[DEBUG] Mock Payment: procesando ${monto} sin cargo real.")
        return True


class PaymentFactory:
    """Selecciona el procesador usando la variable de entorno PAYMENT_PROVIDER."""

    @staticmethod
    def get_processor():
        provider = os.getenv("PAYMENT_PROVIDER", "BANCO").strip().upper()
        if provider == "MOCK":
            return MockPaymentProcessor()
        return BancoNacionalProcesador()
