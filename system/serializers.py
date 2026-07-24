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

class MySubjectsRequestSerializer(serializers.Serializer):
    """Validates that the student is requesting subjects for a class they are actually enrolled in."""
    class_id = serializers.UUIDField(required=True)

    def validate_class_id(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            is_enrolled = Enrollment.objects.filter(
                student=request.user, 
                class_obj_id=value
            ).exists()
            
            if not is_enrolled:
                raise serializers.ValidationError("You are not enrolled in this class.")
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
        try:
            student = User.objects.get(student_id=value, role='student')
        except User.DoesNotExist:
            raise serializers.ValidationError("Student with this Roll Number not found.")
        return student

    def validate_subject_code(self, value):
        try:
            subject = Subject.objects.get(code=value.upper())
        except Subject.DoesNotExist:
            raise serializers.ValidationError("Subject with this code not found.")
        return subject

    def validate(self, data):
        student = data.get('student_roll_no')
        subject = data.get('subject_code')
        exam_type = data.get('exam_type')
        obtained_marks = data.get('obtained_marks')

        if Grade.objects.filter(
            student=student,
            subject=subject,
            exam_type=exam_type
        ).exists():
            raise serializers.ValidationError({
                "exam_type": "Grade already entered for this exam type. Please update the existing grade instead."
            })

        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if not subject.teachers.filter(id=request.user.id).exists():
                raise serializers.ValidationError({
                    "subject_code": "You are not assigned to teach this subject."
                })

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
        request = self.context.get('request')
        
        return Grade.objects.create(
            student=student, 
            subject=subject,
            teacher=request.user, 
            **validated_data
        )
class ClassSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'section', 'batch_name', 
            'academic_year', 'class_code'
        ]

class SubjectBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'code', 'name']

class ClassSummarySerializer(serializers.ModelSerializer):
    subjects = SubjectBriefSerializer(many=True, read_only=True) 

    class Meta:
        model = Class
        fields = [
            'id', 'name', 'section', 'batch_name', 
            'academic_year', 'class_code', 'subjects' 
        ]

class MyEnrollmentSerializer(serializers.ModelSerializer):
    class_details = ClassSummarySerializer(source='class_obj', read_only=True)
    joined_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'class_details', 'joined_at']

class TeacherSubjectSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    section = serializers.CharField(source='class_obj.section', read_only=True)
    academic_year = serializers.CharField(source='class_obj.academic_year', read_only=True)
    batch_name = serializers.CharField(source='class_obj.batch_name', read_only=True)

    class Meta:
        model = Subject
        fields = [
            'id', 'code', 'name', 'full_marks', 'pass_marks',
            'class_name', 'section', 'academic_year', 'batch_name'
        ]