from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
import time

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        username = extra_fields.get("username")
        
        # Auto-generate username from email or phone if not provided
        if not username:
            if email:
                username = email.split('@')[0]
            elif phone_number:
                username = phone_number
            else:
                raise ValueError("Email or phone number is required.")

        extra_fields["username"] = username
        user = self.model(email=email, phone_number=phone_number, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, phone_number, password, **extra_fields)

    def create_superuser(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, phone_number, password, **extra_fields)

class RoleChoices(models.TextChoices):
    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"
    ADMIN = "admin", "Administrator"

class User(AbstractUser):
    # Removed default Django groups/permissions to use your custom ones
    groups = None
    user_permissions = None

    # --- Core Authentication Fields ---
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=150, null=True, blank=True, unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
    # --- Education Specific Fields ---
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.STUDENT)
    student_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    enrollment_year = models.IntegerField(null=True, blank=True)
    
    # --- Profile Fields ---
    profile_image = models.URLField(null=True, blank=True)
    avatar_image = models.ImageField(upload_to="avatars/", null=True, blank=True)

    # Custom permissions (kept from your original architecture)
    permissions = models.ManyToManyField(
        "accounts.RolePermission", 
        related_name="users",
        blank=True,
    )

    objects = CustomUserManager()

    # Tells Django to use email for login instead of username
    USERNAME_FIELD = "email" 
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.get_role_display()})"

    @property
        def is_student(self): 
            return self.role == RoleChoices.STUDENT
    
    @property
        def is_teacher(self): 
            return self.role == RoleChoices.TEACHER

    @cached_property
    def get_roles(self) -> list[dict]:
        """
        Maps user to their Courses/Academic Years.
        """
        start_time = time.time()
        
        if self.is_student:
            roles_qs = (
                self.enrollments.filter(is_active=True)
                .select_related("course", "academic_year")
                .values("course__name", "course__code", "academic_year__name")
            )
            mapped = [{"role": "STUDENT", "course": r["course__name"], "code": r["course__code"], "year": r["academic_year__name"]} for r in roles_qs]
            
        elif self.is_teacher:
            roles_qs = (
                self.assignments.filter(is_active=True)
                .select_related("course", "academic_year")
                .values("course__name", "course__code", "academic_year__name")
            )
            mapped = [{"role": "TEACHER", "course": r["course__name"], "code": r["course__code"], "year": r["academic_year__name"]} for r in roles_qs]
        else:
            mapped = [{"role": "ADMIN"}]

        end_time = time.time()
        print(f"get_roles executed in {end_time - start_time:.4f} seconds")
        return mapped

    @cached_property
    def get_permissions(self) -> list[dict]:
        all_perms = []
        for perms in self.permissions.all():
            all_perms.append({
                "name": perms.permission.name,
                "url_name": perms.permission.url_name,
                "method": perms.permission.method,
                "id": perms.permission.id,
            })
        return all_perms