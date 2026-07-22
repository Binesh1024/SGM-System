from django.urls import path
from .views import JoinClassView, MySubjectsView,GradeEntryView, StudentTranscriptView
urlpatterns = [
   
    path('classes/join/', JoinClassView.as_view(), name='join-class'),
    path('subjects/my-subjects/', MySubjectsView.as_view(), name='my-subjects'),
    path('grades/enter/', GradeEntryView.as_view(), name='enter-grade'),
    path('transcript/my-transcript/', StudentTranscriptView.as_view(),  name='my-transcript'),

]