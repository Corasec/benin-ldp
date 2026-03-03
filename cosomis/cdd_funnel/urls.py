from django.urls import path
from rest_framework import routers

from cdd_funnel.views import CddFunnelView, CddFunnelCsvView

router = routers.DefaultRouter()

app_name = 'cdd_funnel'
urlpatterns = [
    path('', CddFunnelView.as_view(), name='main_funnel'),
    path('export/csv/', CddFunnelCsvView.as_view(), name='export_csv'),
]
