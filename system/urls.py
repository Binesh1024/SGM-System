from django.urls import path
from .views import ClassDashboardView,ClassStudentsListView

urlpatterns = [
   
    path('classes/dashboard/', ClassDashboardView.as_view(), name='class-dashboard'),
    path('classes/<uuid:class_id>/students/', ClassStudentsListView.as_view(), name='class-students'),

]