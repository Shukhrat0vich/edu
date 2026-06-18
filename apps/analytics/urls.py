"""URL configuration for analytics app."""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('overview/', views.AnalyticsOverviewView.as_view(), name='overview'),
    path('correlation/', views.CorrelationView.as_view(), name='correlation'),
    path('heatmap/', views.HeatmapView.as_view(), name='heatmap'),
    path('export/excel/', views.ExportExcelView.as_view(), name='export_excel'),
    path('export/pdf/', views.ExportPDFView.as_view(), name='export_pdf'),
]
