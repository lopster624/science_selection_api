from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import DirectionsViewSet, ApplicationViewSet

router = DefaultRouter()
router.register(r'directions', DirectionsViewSet)
router.register(r'applications', ApplicationViewSet)
urlpatterns = [
    path('', include(router.urls))
]
