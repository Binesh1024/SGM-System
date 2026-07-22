import uuid
from django.db import models
from accounts.models import BaseModel, User

class Class(BaseModel):
    name = models.CharField(max_length=100, help_text="e.g., 1st Sem, Class 10")
    section = models.CharField(max_length=10, help_text="e.g., A, B") 
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
    teachers = models.ManyToManyField(
        User,
        limit_choices_to={'role': 'teacher'},
        related_name='taught_subjects',
        blank=True,
        help_text="Select the teacher(s) assigned to teach this subject."
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
        unique_together = ('student', 'class_obj') 

    def __str__(self):
        return f"{self.student.full_name} enrolled in {self.class_obj}"
    

class Grade(BaseModel):
    """
    Stores the marks obtained by a student in a specific subject and exam type.
    """
    EXAM_TYPE_CHOICES = [
        ('Midterm', 'Midterm Exam'),
        ('Final', 'Final Exam'),
        ('Assignment', 'Assignment'),
        ('Quiz', 'Quiz'),
        ('Practical', 'Practical'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='grades',
        limit_choices_to={'role': 'student'}
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='entered_grades',
        limit_choices_to={'role': 'teacher'}
    )
    
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    obtained_marks = models.DecimalField(max_digits=5, decimal_places=2)

    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    letter_grade = models.CharField(max_length=2, blank=True)
    is_passed = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'subject', 'exam_type')
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} ({self.exam_type}): {self.obtained_marks}"

    def save(self, *args, **kwargs):
        """Auto-calculate percentage, pass/fail, and letter grade before saving."""
        if self.subject.full_marks > 0:
            self.percentage = round((self.obtained_marks / self.subject.full_marks) * 100, 2)
        else:
            self.percentage = 0.00
        self.is_passed = self.obtained_marks >= self.subject.pass_marks
        if self.percentage >= 90:
            self.letter_grade = 'A+'
        elif self.percentage >= 80:
            self.letter_grade = 'A'
        elif self.percentage >= 70:
            self.letter_grade = 'B'
        elif self.percentage >= 60:
            self.letter_grade = 'C'
        elif self.percentage >= 50:
            self.letter_grade = 'D'
        else:
            self.letter_grade = 'F'

        super().save(*args, **kwargs)