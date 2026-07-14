import uuid
from django.db import models
from accounts.models import BaseModel, User

class Class(BaseModel):
    name = models.CharField(max_length=100, help_text="e.g., 1st Sem, Class 10")
    section = models.CharField(max_length=10, help_text="e.g., A, B") # 👈 ADDED: Was missing but used in Meta
    academic_year = models.CharField(max_length=20, help_text="e.g., 2026")
    batch_name = models.CharField(max_length=100, help_text="e.g., Batch 2026, Group A")
    class_code = models.CharField(
        max_length=10, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Auto-generated code for students to join this batch."
    )

    class Meta:
        unique_together = ('name', 'section', 'academic_year')

    def save(self, *args, **kwargs):
        if not self.class_code:
            self.class_code = str(uuid.uuid4())[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.section} ({self.batch_name})"


class Subject(BaseModel):
    name = models.CharField(max_length=100, help_text="e.g., Mathematics, Physics")
    code = models.CharField(max_length=20, unique=True, help_text="e.g., MATH101")
    full_marks = models.IntegerField(default=100)
    pass_marks = models.IntegerField(default=40)
    class_obj = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='subjects',
        help_text="Which batch/class is this subject taught to?"
    )

    def __str__(self):
        return f"{self.code} - {self.name} ({self.class_obj.name})"
    
class Enrollment(BaseModel):
    """
    Tracks which student is enrolled in which Class (Batch).
    """
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='class_enrollments',
        limit_choices_to={'role': 'student'}
    )
    class_obj = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='enrollments'
    )

    class Meta:
        unique_together = ('student', 'class_obj') # Prevent joining the same class twice

    def __str__(self):
        return f"{self.student.full_name} enrolled in {self.class_obj}"