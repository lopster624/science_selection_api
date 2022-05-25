from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import DirectionsViewSet, ApplicationViewSet, EducationViewSet, CompetenceViewSet, BookingViewSet, \
    WishlistViewSet, WorkGroupViewSet, DownloadServiceDocuments, DirectionsCompetences, ApplicationNoteViewSet, \
    FileViewSet

router = DefaultRouter()
router.register(r'directions', DirectionsViewSet)
router.register(r'applications', ApplicationViewSet, basename='applications')
router.register(r'competences', CompetenceViewSet)
router.register(r'files', FileViewSet, basename='files')
router.register(r'work-groups', WorkGroupViewSet, basename='work-groups')

domains_router = routers.NestedSimpleRouter(router, r'applications', lookup='application')
domains_router.register(r'educations', EducationViewSet, basename='educations')
domains_router.register(r'booking', BookingViewSet, basename='booking')
domains_router.register(r'wishlist', WishlistViewSet, basename='wishlist')
domains_router.register(r'notes', ApplicationNoteViewSet, basename='notes')

urlpatterns = [
    path(r'download-files/', DownloadServiceDocuments.as_view(), name='download-file'),
    path(r'directions/<int:direction_id>/competences/', DirectionsCompetences.as_view(), name='direction-competences'),
    path(r'', include(router.urls)),
    path(r'', include(domains_router.urls)),
]
