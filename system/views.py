from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from .models import Class
from .serializers import ClassSerializer, StudentListSerializer, ClassDashboardResponseSerializer,ClassStudentsResponseSerializer
from accounts.models import RoleChoices, User

@extend_schema(
    summary="Get Class Dashboard Statistics",
    description="Retrieve the total number of classes, total enrolled students, "
                "and detailed statistics for each class.",
    responses={200: ClassDashboardResponseSerializer},
)
class ClassDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
    
        classes_qs = Class.objects.annotate(
            student_count=Count('students')
        ).order_by('-academic_year', 'name')

        total_classes = classes_qs.count()
        total_students = sum(c.student_count for c in classes_qs)

        serializer = ClassSerializer(classes_qs, many=True)

        return Response({
            "total_classes": total_classes,
            "total_students_enrolled": total_students,
            "classes": serializer.data
        }, status=status.HTTP_200_OK)

@extend_schema(
    summary="List Students in a Specific Class",
    description="Retrieve a detailed list of all students enrolled in a specific class.",
    parameters=[
        OpenApiParameter(
            name='class_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description="The unique UUID of the class."
        )
    ],
    responses={200: ClassStudentsResponseSerializer},
)
class ClassStudentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, class_id):
        class_obj = get_object_or_404(Class, id=class_id)

        students = User.objects.filter(
            current_class=class_obj,
            role=RoleChoices.STUDENT
        ).order_by('first_name', 'last_name')

        return Response({
            "class_details": ClassSerializer(class_obj).data,
            "total_students": students.count(),
            "students": StudentListSerializer(students, many=True).data
        }, status=status.HTTP_200_OK)