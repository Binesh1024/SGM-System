from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema,OpenApiParameter, OpenApiTypes
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from accounts.models import User
from .models import Class, Subject, Enrollment, Grade
from .serializers import JoinClassSerializer, SubjectListSerializer,GradeEntrySerializer, MyEnrollmentSerializer,TeacherSubjectSerializer


@extend_schema(
    summary="Join a Class (Batch)",
    description="Student joins a class using the auto-generated class_code.",
    request=JoinClassSerializer,
    responses={200: {"message": "string"}},
)
class JoinClassView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_student:
            return Response({"error": "Only students can join classes."}, status=403)

        serializer = JoinClassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        class_code = serializer.validated_data['class_code']

        class_obj = Class.objects.get(class_code=class_code)

        try:
            Enrollment.objects.create(student=request.user, class_obj=class_obj)
            return Response({
                "message": f"Successfully joined {class_obj.name} - {class_obj.section}!"
            }, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"error": "You are already enrolled in this class."}, status=400)

@extend_schema(
    summary="Get My Subjects",
    description="Returns all subjects for the class the student has joined.",
    responses={200: SubjectListSerializer(many=True)},
)
class MySubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response({"error": "Access denied."}, status=403)
        enrollment = Enrollment.objects.filter(student=request.user).first()
        
        if not enrollment:
            return Response({"message": "You haven't joined any class yet."}, status=200)
        subjects = Subject.objects.filter(class_obj=enrollment.class_obj)
        
        serializer = SubjectListSerializer(subjects, many=True)
        return Response({
            "current_class": f"{enrollment.class_obj.name} - {enrollment.class_obj.section}",
            "subjects": serializer.data
        }, status=status.HTTP_200_OK)

@extend_schema(
    summary="Enter Student Grade",
    description="Allows an assigned teacher to enter obtained marks for a student.",
    request=GradeEntrySerializer,
    responses={201: GradeEntrySerializer},
)
class GradeEntryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_teacher:
            return Response(
                {"error": "Only teachers can enter grades."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = GradeEntrySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        grade = serializer.save()

        return Response({
            "message": "Grade entered successfully.",
            "grade_details": {
                "student": grade.student.full_name,
                "subject": grade.subject.name,
                "exam_type": grade.exam_type,
                "obtained_marks": float(grade.obtained_marks),
                "letter_grade": grade.letter_grade,
                "is_passed": grade.is_passed
            }
        }, status=status.HTTP_201_CREATED)
    


@extend_schema(
    summary="Get Student Transcript",
    description="Returns all subjects for the student's enrolled class along with their grades.",
    responses={200: {"type": "object"}}, 
)
class StudentTranscriptView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response({"error": "Only students can view their transcript."}, status=403)

        enrollment = Enrollment.objects.filter(student=request.user).select_related('class_obj').first()
        
        if not enrollment:
            return Response({"message": "You are not enrolled in any class yet."}, status=200)

        class_obj = enrollment.class_obj

        subjects = Subject.objects.filter(class_obj=class_obj)
        
        grades = Grade.objects.filter(student=request.user, subject__in=subjects)
        grades_dict = {grade.subject_id: grade for grade in grades}

        transcript_subjects = []
        total_obtained = 0.0
        total_full = 0.0 
        all_passed = True
        has_pending_grades = False  

        for subject in subjects:
            total_full += subject.full_marks
            grade = grades_dict.get(subject.id)

            if grade:
                total_obtained += float(grade.obtained_marks)
                if not grade.is_passed:
                    all_passed = False
                
                transcript_subjects.append({
                    "subject_name": subject.name,
                    "subject_code": subject.code,
                    "obtained_marks": float(grade.obtained_marks),
                    "full_marks": subject.full_marks,
                    "letter_grade": grade.letter_grade,
                    "is_passed": grade.is_passed
                })
            else:

                has_pending_grades = True  
                transcript_subjects.append({
                    "subject_name": subject.name,
                    "subject_code": subject.code,
                    "obtained_marks": None,
                    "full_marks": subject.full_marks,
                    "letter_grade": "N/A",
                    "is_passed": None
                })

        if has_pending_grades:
            overall_status = "Pending"
        elif all_passed:
            overall_status = "Pass"
        else:
            overall_status = "Fail"

        return Response({
            "student_info": {
                "name": request.user.full_name,
                "student_id": request.user.student_id,
                "email": request.user.email
            },
            "class_info": {
                "name": class_obj.name,
                "section": class_obj.section,
                "batch": class_obj.batch_name,
                "academic_year": class_obj.academic_year
            },
            "summary": {
                "total_obtained_marks": total_obtained,
                "total_full_marks": total_full,
                "overall_status": overall_status 
            },
            "subjects": transcript_subjects
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get My Classes",
    description="Returns all the classes the logged-in student has successfully joined.",
    responses={200: MyEnrollmentSerializer(many=True)},
)
class MyClassesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response(
                {"error": "Only students can view their enrolled classes."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        enrollments = Enrollment.objects.filter(
            student=request.user
        ).select_related('class_obj').order_by('-created_at')
        serializer = MyEnrollmentSerializer(enrollments, many=True)
        
        return Response({
            "total_enrolled_classes": enrollments.count(),
            "my_classes": serializer.data
        }, status=status.HTTP_200_OK)

@extend_schema(
    summary="Get My Assigned Subjects",
    description="Returns all subjects the logged-in teacher is assigned to teach, along with class details.",
    responses={200: TeacherSubjectSerializer(many=True)},
)
class TeacherAssignedSubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_teacher:
            return Response({"error": "Only teachers can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)
        subjects = Subject.objects.filter(
            teachers=request.user
        ).select_related('class_obj').order_by('class_obj__name', 'code')
        
        serializer = TeacherSubjectSerializer(subjects, many=True)
        
        return Response({
            "total_assigned_subjects": subjects.count(),
            "subjects": serializer.data
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Get Students in a Subject",
    description="Returns all students enrolled in the class for a specific subject, including their current grade (if entered).",
    parameters=[
        OpenApiParameter(
            name='subject_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description="The UUID of the subject."
        )
    ],
    responses={200: {"type": "object"}},
)
class SubjectStudentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subject_id):
        if not request.user.is_teacher:
            return Response({"error": "Only teachers can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)
        try:
            subject = Subject.objects.select_related('class_obj').get(id=subject_id)
        except Subject.DoesNotExist:
            return Response({"error": "Subject not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if not subject.teachers.filter(id=request.user.id).exists():
            return Response({"error": "You are not assigned to teach this subject."}, status=status.HTTP_403_FORBIDDEN)
        enrollments = Enrollment.objects.filter(
            class_obj=subject.class_obj
        ).select_related('student').order_by('student__first_name', 'student__last_name')
        student_ids = [enrollment.student_id for enrollment in enrollments]
        grades = Grade.objects.filter(
            subject=subject, 
            student_id__in=student_ids
        )
        grades_dict = {grade.student_id: grade for grade in grades}
        students_data = []
        for enrollment in enrollments:
            student = enrollment.student
            grade = grades_dict.get(student.id)
            
            students_data.append({
                "id": str(student.id),
                "student_id": student.student_id,
                "full_name": student.full_name,
                "email": student.email,
                "grade": {
                    "exam_type": grade.exam_type,
                    "obtained_marks": float(grade.obtained_marks),
                    "letter_grade": grade.letter_grade,
                    "is_passed": grade.is_passed
                } if grade else None 
            })
            
        return Response({
            "subject_info": {
                "id": str(subject.id),
                "code": subject.code,
                "name": subject.name,
                "class": f"{subject.class_obj.name} - {subject.class_obj.section} ({subject.class_obj.batch_name})"
            },
            "total_students": len(students_data),
            "students": students_data
        }, status=status.HTTP_200_OK)