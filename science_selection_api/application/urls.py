from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import DirectionsViewSet, ApplicationViewSet, EducationViewSet, CompetenceViewSet

router = DefaultRouter()
router.register(r'directions', DirectionsViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'competences', CompetenceViewSet)

domains_router = routers.NestedSimpleRouter(router, r'applications', lookup='application')
domains_router.register(r'educations', EducationViewSet, basename='educations')


urlpatterns = [
    path('', include(router.urls)),
    path(r'', include(domains_router.urls)),
]
