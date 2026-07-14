from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from accounts.models import User
from .models import Class, Subject, Enrollment
from .serializers import JoinClassSerializer, SubjectListSerializer



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