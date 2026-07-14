import uuid
from django.db import models
from django.conf import settings
from accounts.models import BaseModel

class Class(BaseModel):
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=10)
    academic_year = models.CharField(max_length=20)
    class_code = models.CharField(max_length=10, unique=True, blank=True, null=True)

    class Meta:
        unique_together = ('name', 'section', 'academic_year')

    def save(self, *args, **kwargs):
        if not self.class_code:
            self.class_code = str(uuid.uuid4())[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.section} ({self.academic_year})"   