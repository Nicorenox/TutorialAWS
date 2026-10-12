from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tienda_app.infra.factories import PaymentFactory
from tienda_app.models import Inventario, Libro
from tienda_app.services import CompraService

from .serializers import OrdenInputSerializer


class CompraAPIView(APIView):
    """
    Endpoint para procesar compras via JSON.
    POST /api/v1/comprar/
    Payload: {"libro_id": 1, "direccion_envio": "Calle 123", "cantidad": 1}
    """

    def get(self, request):
        """Permite verificar desde el navegador que la API desplegada responde."""
        libros = Libro.objects.all().order_by('id')
        inventarios = {
            item.libro_id: item.cantidad
            for item in Inventario.objects.filter(libro__in=libros)
        }
        return Response({
            'api': 'Tienda API',
            'estado': 'disponible',
            'endpoint_compra': '/api/v1/comprar/',
            'metodo_compra': 'POST',
            'libros': [
                {
                    'id': libro.id,
                    'titulo': libro.titulo,
                    'precio': str(libro.precio),
                    'stock_actual': inventarios.get(libro.id, 0),
                }
                for libro in libros
            ],
        })

    def post(self, request):
        serializer = OrdenInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data

        try:
            gateway = PaymentFactory.get_processor()
            servicio = CompraService(procesador_pago=gateway)
            usuario = request.user if request.user.is_authenticated else None
            libro = Libro.objects.get(id=datos['libro_id'])
            inventario_antes = Inventario.objects.filter(libro=libro).first()
            stock_antes = inventario_antes.cantidad if inventario_antes else 0

            resultado = servicio.ejecutar_compra(
                libro_id=datos['libro_id'],
                cantidad=datos.get('cantidad', 1),
                direccion=datos['direccion_envio'],
                usuario=usuario,
            )

            inventario_despues = Inventario.objects.filter(libro=libro).first()
            stock_despues = inventario_despues.cantidad if inventario_despues else 0
            cantidad_comprada = datos.get('cantidad', 1)

            return Response(
                {
                    'estado': 'exito',
                    'mensaje': f'Orden creada. Total: {resultado}',
                    'libro': libro.titulo,
                    'cantidad_comprada': cantidad_comprada,
                    'stock_antes': stock_antes,
                    'stock_despues': stock_despues,
                    'inventario_descontado': stock_antes - stock_despues,
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception:
            return Response({'error': 'Error interno'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
