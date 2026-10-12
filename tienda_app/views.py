from django.shortcuts import render
from django.views import View

from .infra.factories import PaymentFactory
from .models import Inventario, Libro
from .services import CompraService


class CompraView(View):
    """La vista recibe la petición y delega el proceso al servicio."""

    template_name = "tienda_app/compra.html"

    def setup_service(self):
        return CompraService(procesador_pago=PaymentFactory.get_processor())

    def get(self, request, libro_id):
        contexto = self.setup_service().obtener_detalle_producto(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            usuario = request.user if request.user.is_authenticated else None
            total = servicio.ejecutar_compra(libro_id, cantidad=1, usuario=usuario)
            contexto = servicio.obtener_detalle_producto(libro_id)
            contexto["mensaje_exito"] = f"¡Gracias por su compra! Total: ${total}"
            return render(request, self.template_name, contexto)
        except Exception as error:
            contexto = servicio.obtener_detalle_producto(libro_id)
            contexto["error"] = str(error)
            return render(request, self.template_name, contexto, status=400)


def compra_rapida_fbv(request, libro_id):
    servicio = CompraService(procesador_pago=PaymentFactory.get_processor())
    if request.method == "POST":
        try:
            usuario = request.user if request.user.is_authenticated else None
            total = servicio.ejecutar_compra(libro_id, cantidad=1, usuario=usuario)
            contexto = servicio.obtener_detalle_producto(libro_id)
            contexto["mensaje_exito"] = f"Compra exitosa. Total pagado: ${total}"
            return render(request, "tienda_app/compra_rapida.html", contexto)
        except Exception as error:
            contexto = servicio.obtener_detalle_producto(libro_id)
            contexto["error"] = str(error)
            return render(request, "tienda_app/compra_rapida.html", contexto, status=400)

    return render(
        request,
        "tienda_app/compra_rapida.html",
        servicio.obtener_detalle_producto(libro_id),
    )


def home(request):
    # Se consulta el inventario real para mostrarlo en la tienda.
    libros = list(Libro.objects.all().order_by("id"))
    inventarios = {
        item.libro_id: item.cantidad
        for item in Inventario.objects.filter(libro_id__in=[libro.id for libro in libros])
    }
    for libro in libros:
        libro.stock_actual = inventarios.get(libro.id, 0)
    return render(request, "tienda_app/home.html", {"libros": libros})
