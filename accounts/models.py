import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .manager import CustomUserManager

class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active_record = models.BooleanField(default=True)

    class Meta:
        abstract = True

class RoleChoices(models.TextChoices):
    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"
    ADMIN = "admin", "Administrator"


class User(AbstractBaseUser, PermissionsMixin,BaseModel):
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, null=True, blank=True, unique=True)
    is_email_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT,
    )
    student_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    enrollment_year = models.IntegerField(null=True, blank=True)
    profile_image = models.URLField(null=True, blank=True)
    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="custom_users",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="custom_users",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"] 

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_student(self):
        return self.role == RoleChoices.STUDENT

    @property
    def is_teacher(self):
        return self.role == RoleChoices.TEACHER

    @property
    def is_admin(self):
        return self.role == RoleChoices.ADMIN