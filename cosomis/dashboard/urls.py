from django.urls import path
from django.conf.urls import include

from . import views_subprojects, views_excel, views_administrativelevels

app_name = 'dashboard'

urlpatterns = [
    path('', views_subprojects.DashboardTemplateView.as_view(), name='dashboard'),
    path('subprojects/', views_subprojects.DashboardTemplateView.as_view(), name='dashboard_subprojects'),
    path('administrativelevels/', views_administrativelevels.DashboardTemplateView.as_view(), name='dashboard_administrativelevels'),
    
    path('subprojects-sectors/', views_subprojects.DashboardSubprojectsListView.as_view(), name='dashboard_subprojects_sectors'),
    path('subprojects-sectors-and-steps/', views_subprojects.DashboardSubprojectsSectorsAndStepsListView.as_view(), name='dashboard_subprojects_sectors_and_steps'),
    path('subprojects-steps/', views_subprojects.DashboardSubprojectsStepsListView.as_view(), name='dashboard_subprojects_steps'),
    
    path('waves/', views_administrativelevels.DashboardWaveListView.as_view(), name='dashboard_waves'),
    path('summary-administrativel-levels-number/', views_administrativelevels.DashboardSummaryAdministrativeLevelNumberListView.as_view(), name='dashboard_summary_administrativel_levels_number'),
    path('summary-allocation/', views_administrativelevels.DashboardSummaryAdministrativeLevelAllocationListView.as_view(), name='dashboard_summary_allocation'),

    path('download-excel-file/', views_excel.DownloadExcelFile.as_view(), name='dashboard_download_excel_file'),
]
