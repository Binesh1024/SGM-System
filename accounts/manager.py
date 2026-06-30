import logging
from django.contrib.auth.base_user import BaseUserManager

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        
        email = self.normalize_email(email)
        extra_fields.setdefault("username", email.split("@")[0])
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        logger.info(f"Created user: {user.email}")
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # Use string literal instead of RoleChoices.ADMIN to avoid circular import
        extra_fields.setdefault("role", "admin")
        
        return self._create_user(email, password, **extra_fields)