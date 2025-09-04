from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .utils.export_utils import export_pdf, export_print_view

urlpatterns = [
    path('', views.home, name='home'),
    path('forensic-analysis/', views.forensic_analysis, name='forensic_analysis'),
    path('upload/', views.upload_image, name='upload_image'),  # Add this line
    path('api/predict/', views.api_predict, name='api_predict'),
    path('report/pdf/<int:analysis_id>/', export_pdf, name='export_pdf'),
    path('report/print/<int:analysis_id>/', export_print_view, name='print_report'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)