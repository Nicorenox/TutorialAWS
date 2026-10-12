from django.urls import path
from .api.views import CompraAPIView
from .views import CompraView, compra_rapida_fbv, home

urlpatterns = [
    path("", home, name="home"),

    path(
        "compra/<int:libro_id>/",
        CompraView.as_view(),
        name="finalizar_compra"
    ),

    path(
        "compra-fbv/<int:libro_id>/",
        compra_rapida_fbv,
        name="compra_rapida_fbv"
    ),

    path(
        "api/v1/comprar/",
        CompraAPIView.as_view(),
        name="api_comprar"
    ),
]