from rest_framework import serializers
from .models import Class, Subject, Grade, Enrollment
from accounts.models import User

class JoinClassSerializer(serializers.Serializer):
    class_code = serializers.CharField(max_length=10, required=True)

    def validate_class_code(self, value):
        value = value.strip().upper()
        if not Class.objects.filter(class_code=value).exists():
            raise serializers.ValidationError("Invalid class code. Please check and try again.")
        return value

class SubjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'full_marks', 'pass_marks']

class GradeEntrySerializer(serializers.ModelSerializer):
    student_roll_no = serializers.CharField(required=True, write_only=True)
    subject_code = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Grade
        fields = ['student_roll_no', 'subject_code', 'exam_type', 'obtained_marks', 'remarks']

    def validate_student_roll_no(self, value):
        """Find the student using their custom Roll Number."""
        try:
            student = User.objects.get(student_id=value, role='student')
        except User.DoesNotExist:
            raise serializers.ValidationError("Student with this Roll Number not found.")
        return student

    def validate_subject_code(self, value):
        """Find the subject using its unique code (case-insensitive)."""
        try:
            subject = Subject.objects.get(code=value.upper())
        except Subject.DoesNotExist:
            raise serializers.ValidationError("Subject with this code not found.")
        return subject

    def validate(self, data):
        student = data.get('student_roll_no') 
        subject = data.get('subject_code')  
        obtained_marks = data.get('obtained_marks')
        if obtained_marks > subject.full_marks:
            raise serializers.ValidationError({
                "obtained_marks": f"Marks cannot exceed {subject.full_marks}."
            })
        if obtained_marks < 0:
            raise serializers.ValidationError({"obtained_marks": "Marks cannot be negative."})

        is_enrolled = Enrollment.objects.filter(
            student=student, 
            class_obj=subject.class_obj
        ).exists()
        
        if not is_enrolled:
            raise serializers.ValidationError({
                "student_roll_no": "This student is not enrolled in the class for this subject."
            })

        return data

    def create(self, validated_data):
        student = validated_data.pop('student_roll_no')
        subject = validated_data.pop('subject_code')
        return Grade.objects.create(
            student=student, 
            subject=subject, 
            **validated_data
        )