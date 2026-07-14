from rest_framework import serializers
from .models import Class
from accounts.models import User

# class ClassStatsSerializer(serializers.ModelSerializer):
#     student_count = serializers.IntegerField(read_only=True)

#     class Meta:
#         model = Class
#         fields = [
#             'id', 'name', 'section', 'academic_year', 
#             'class_code', 'student_count'
#         ]

from rest_framework import serializers
from .models import Class

class ClassSerializer(serializers.ModelSerializer):
    """
    Serializer for Class model.
    Handles creation, validation, and reading (including annotated student_count).
    """
    # This field is only populated when the queryset is annotated (e.g., in Dashboard)
    student_count = serializers.IntegerField(
        read_only=True, 
        required=False, 
        default=0,
        help_text="Number of students in this class (only available in dashboard endpoints)."
    )

    class Meta:
        model = Class
        fields = [
            'id', 
            'name', 
            'section', 
            'academic_year', 
            'class_code', 
            'student_count', 
            'created_at', 
            'updated_at'
        ]
        # These fields are generated automatically and cannot be set by the user
        read_only_fields = ['id', 'class_code', 'created_at', 'updated_at', 'student_count']
        extra_kwargs = {
            'name': {'required': True},
            'section': {'required': True},
            'academic_year': {'required': True},
        }

    def validate_section(self, value):
        """Automatically convert section to uppercase."""
        return value.upper().strip()

    def validate_academic_year(self, value):
        """Ensure academic year follows the 'YYYY-YYYY' format."""
        value = value.strip()
        if not value or '-' not in value:
            raise serializers.ValidationError(
                "Academic year must be in 'YYYY-YYYY' format (e.g., '2025-2026')."
            )
        return value


class StudentListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'student_id', 'phone_number', 'enrollment_year', 
            'is_email_verified', 'profile_image'
        ]
class ClassDashboardResponseSerializer(serializers.Serializer):
    total_classes = serializers.IntegerField()
    total_students_enrolled = serializers.IntegerField()
    classes = ClassSerializer(many=True)


class ClassStudentsResponseSerializer(serializers.Serializer):
    class_details = ClassSerializer()
    total_students = serializers.IntegerField()
    students = StudentListSerializer(many=True)