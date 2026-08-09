from django.urls import path
from .views import RetrieveBaseInfos


urlpatterns = [
        path('base-info/', RetrieveBaseInfos.as_view(), name="base_info")

]