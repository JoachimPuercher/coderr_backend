from django.urls import path
from .views import OfferListCreateView, OfferDetailRetrieveView, OfferSingleView


urlpatterns = [
    path('offers/', OfferListCreateView.as_view(), name='offer'),
    path('offers/<int:id>/', OfferSingleView.as_view(), name='singleoffer'),
    path('offerdetails/<int:id>/', OfferDetailRetrieveView.as_view(), name='offerdetails')
]


# /api/offers - POST am Ende fertig bauen - nested detail serializer sobald die offerdetail view steht.