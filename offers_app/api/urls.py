from django.urls import path
from .views import OfferMainView


urlpatterns = [
    path('offers/', OfferMainView.as_view(), name='offer')
    # path('offers/<int:id>/', OfferDetailView.as_view(), name='offer_detail'),
]