from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema,OpenApiParameter, OpenApiTypes
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from accounts.models import User
from .models import Class, Subject, Enrollment, Grade,get_subject_final_grade
from .serializers import JoinClassSerializer, MySubjectsRequestSerializer, SubjectListSerializer,GradeEntrySerializer, MyEnrollmentSerializer,TeacherSubjectSerializer
from django.utils import timezone

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
    summary="Get Subjects for a Specific Class",
    description="Returns all subjects for a specific class that the student has joined.",
    request=MySubjectsRequestSerializer,
    responses={200: SubjectListSerializer(many=True)},
)
class MySubjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_student:
            return Response({"error": "Access denied. Students only."}, status=status.HTTP_403_FORBIDDEN)

        serializer = MySubjectsRequestSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        class_id = serializer.validated_data['class_id']
        class_obj = get_object_or_404(Class, id=class_id)
        subjects = Subject.objects.filter(class_obj=class_obj)
        subject_serializer = SubjectListSerializer(subjects, many=True)

        return Response({
            "class_info": {
                "id": str(class_obj.id),
                "name": class_obj.name,
                "section": class_obj.section,
                "batch_name": class_obj.batch_name,
                "academic_year": class_obj.academic_year
            },
            "total_subjects": subjects.count(),
            "subjects": subject_serializer.data
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
        final_grade_data = get_subject_final_grade(grade.student, grade.subject)

        response_data = {
            "message": "Grade entered successfully.",
            "grade_details": {
                "student": grade.student.full_name,
                "subject": grade.subject.name,
                "exam_type": grade.exam_type,
                "obtained_marks": float(grade.obtained_marks),
                "letter_grade": grade.letter_grade,
                "is_passed": grade.is_passed
            }
        }
        if final_grade_data:
            response_data["final_subject_grade"] = final_grade_data
            response_data["message"] += " Final subject grade calculated."
        else:
            response_data["message"] += " Waiting for remaining exam types to calculate final grade."

        return Response(response_data, status=status.HTTP_201_CREATED)
    


@extend_schema(
    summary="Download/View Student Transcript",
    description="Returns the live transcript. If class_id is provided, returns the detailed transcript for that class. If omitted, returns a list of all enrolled classes.",
    parameters=[
        OpenApiParameter(
            name='class_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description="Optional: The UUID of the specific class to get the transcript for."
        )
    ],
    responses={200: {"type": "object"}},
)

class StudentTranscriptView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response({"error": "Only students can view their transcript."}, status=status.HTTP_403_FORBIDDEN)

        requested_class_id = request.query_params.get('class_id')

        if requested_class_id:

            enrollment = Enrollment.objects.filter(
                student=request.user, 
                class_obj_id=requested_class_id
            ).select_related('class_obj').first()

            if not enrollment:
                return Response(
                    {"error": "You are not enrolled in this class, or the class ID is invalid."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            

            return self._generate_single_transcript(request.user, enrollment.class_obj)

        enrollments = Enrollment.objects.filter(
            student=request.user
        ).select_related('class_obj').order_by('-created_at')

        if not enrollments.exists():
            return Response({"message": "You are not enrolled in any classes yet."}, status=status.HTTP_200_OK)

        classes_summary = []
        for enrollment in enrollments:
            class_obj = enrollment.class_obj
            classes_summary.append({
                "class_id": str(class_obj.id),
                "program": class_obj.name,
                "section": class_obj.section,
                "batch": class_obj.batch_name,
                "academic_year": class_obj.academic_year,
                "enrolled_at": enrollment.created_at.strftime("%Y-%m-%d")
            })

        return Response({
            "message": "Please specify a class_id to download the detailed transcript.",
            "available_classes": classes_summary
        }, status=status.HTTP_200_OK)

    
    def _generate_single_transcript(self, student, class_obj):
        """Helper method to calculate and return the transcript for a specific class."""
        subjects = Subject.objects.filter(class_obj=class_obj)

        transcript_subjects = []
        total_obtained = 0.0
        total_full = 0.0
        all_passed = True
        has_pending_grades = False

        for subject in subjects:
            total_full += 100 
            individual_grades = Grade.objects.filter(student=student, subject=subject)
            final_grade_data = get_subject_final_grade(student, subject)

            if final_grade_data:
                total_obtained += final_grade_data['final_percentage']
                if not final_grade_data['is_passed']:
                    all_passed = False
                
                transcript_subjects.append({
                    "subject_name": subject.name,
                    "subject_code": subject.code,
                    "final_percentage": final_grade_data['final_percentage'],
                    "final_letter_grade": final_grade_data['letter_grade'],
                    "is_passed": final_grade_data['is_passed'],
                    "exam_breakdown": [
                        {
                            "exam_type": g.exam_type,
                            "obtained_marks": float(g.obtained_marks),
                            "full_marks": subject.full_marks,
                            "percentage": float(g.percentage)
                        } for g in individual_grades
                    ]
                })
            else:
                has_pending_grades = True
                transcript_subjects.append({
                    "subject_name": subject.name,
                    "subject_code": subject.code,
                    "final_percentage": None,
                    "final_letter_grade": "Pending",
                    "is_passed": None,
                    "exam_breakdown": [
                        {
                            "exam_type": g.exam_type,
                            "obtained_marks": float(g.obtained_marks),
                            "full_marks": subject.full_marks,
                            "percentage": float(g.percentage)
                        } for g in individual_grades
                    ]
                })

        if has_pending_grades:
            overall_status = "Pending (Incomplete)"
        elif all_passed:
            overall_status = "Pass"
        else:
            overall_status = "Fail"

        return Response({
            "transcript_header": {
                "institution_name": "Your University Name",
                "document_title": "Official Student Transcript",
                "generated_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "student_info": {
                "name": student.full_name,
                "student_id": student.student_id,
                "email": student.email
            },
            "class_info": {
                "program": class_obj.name,
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