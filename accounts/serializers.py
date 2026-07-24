from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from .models import RoleChoices


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number', 
            'role', 'student_id', 'enrollment_year', 'profile_image',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        role = attrs.get('role', RoleChoices.STUDENT)
        student_id = attrs.get('student_id')
        enrollment_year = attrs.get('enrollment_year')
        
        if role == RoleChoices.STUDENT:
            if not student_id:
                raise serializers.ValidationError({
                    "student_id": "Student ID is required for student accounts."
                })
            if not enrollment_year:
                raise serializers.ValidationError({
                    "enrollment_year": "Enrollment year is required for student accounts."
                })
            attrs.pop('teacher_id', None)
            attrs.pop('department', None)
            
        elif role == RoleChoices.TEACHER:
            attrs['student_id'] = None
            attrs['enrollment_year'] = None
            
        elif role == RoleChoices.ADMIN:
            raise serializers.ValidationError({
                "role": "Admin accounts cannot be created through public registration."
            })
        
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'student_id', 'role', 'enrollment_year', 
            # 'profile_image',
        ]
        read_only_fields = [
            'id', 'email', 'student_id', 'role', 
             'full_name'
        ]   