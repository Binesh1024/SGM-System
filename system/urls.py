from django.urls import path
from .views import JoinClassView, MySubjectsView
urlpatterns = [
   
    path('classes/join/', JoinClassView.as_view(), name='join-class'),
    path('subjects/my-subjects/', MySubjectsView.as_view(), name='my-subjects'),

]