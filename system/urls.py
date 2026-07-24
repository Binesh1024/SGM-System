from django.urls import path
from .views import JoinClassView, MySubjectsView,GradeEntryView, StudentTranscriptView, MyClassesView,TeacherAssignedSubjectsView,SubjectStudentsListView
urlpatterns = [
    # Student URLs
    path('student/classes/join/', JoinClassView.as_view(), name='join-class'),
    path('student/classes/my-classes/', MyClassesView.as_view(), name='my-classes'),
    path('student/subjects/my-subjects/', MySubjectsView.as_view(), name='my-subjects'),
    path('student/transcript/download/', StudentTranscriptView.as_view(), name='student-transcript'), 
    
    # Teacher URLs
    path('teachers/grades/enter/', GradeEntryView.as_view(), name='enter-grade'),
    path('teachers/my-subjects/', TeacherAssignedSubjectsView.as_view(), name='teacher-subjects'), 
    path('teachers/subjects/<uuid:subject_id>/students/', SubjectStudentsListView.as_view(), name='subject-students'), 
]