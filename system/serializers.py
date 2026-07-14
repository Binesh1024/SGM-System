from rest_framework import serializers
from .models import Class, Subject

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