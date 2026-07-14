from django.contrib import admin
from .models import Class, Subject, Enrollment

class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 1 
    fields = ('name', 'code', 'full_marks', 'pass_marks')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'section',
        'batch_name',
        'academic_year',
        'class_code',
        'created_at',
    )
    
    list_filter = (
        'academic_year',
        'section',
    )
    
    search_fields = (
        'name',
        'batch_name',
        'class_code',
    )
    
    readonly_fields = (
        'class_code', 
        'created_at',
        'updated_at',
    )
    
    ordering = ('-academic_year', 'name', 'section')

    inlines = [SubjectInline]

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'class_obj',
        'full_marks',
        'pass_marks',
    )
    
    list_filter = (
        'class_obj__academic_year',
        'class_obj__section',
    )
    
    search_fields = (
        'name',
        'code',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    
    ordering = ('code',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'class_obj',
        'created_at',
    )
    
    list_filter = (
        'class_obj',
        'class_obj__academic_year',
    )
    
    search_fields = (
        'student__email',
        'student__first_name',
        'student__last_name',
        'student__student_id',
        'class_obj__name',
    )

    raw_id_fields = ('student',) 
    
    readonly_fields = (
        'created_at',
        'updated_at',
    )