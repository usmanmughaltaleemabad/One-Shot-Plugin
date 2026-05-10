"""
Admin Panel Generator - Auto-generated admin interface

Generates:
- Django admin configuration
- Admin list views, filters, search
- Admin forms and actions
- Custom admin interfaces
"""

from typing import Dict, Any


class AdminPanelGenerator:
    """Generate admin panel code"""

    def __init__(self, framework: str, model_name: str):
        self.framework = framework
        self.model_name = model_name

    def generate_django_admin(self) -> str:
        """Generate Django admin interface"""
        return f"""
from django.contrib import admin
from django.utils.html import format_html
from .models import {self.model_name}

@admin.register({self.model_name})
class {self.model_name}Admin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'status_badge')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {{'fields': ('id', 'name', 'description')}}),
        ('Metadata', {{'fields': ('created_at', 'updated_at')}}),
    )

    def status_badge(self, obj):
        '''Display status badge'''
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px;">Active</span>'
        )
    status_badge.short_description = 'Status'

    actions = ['make_inactive', 'make_active', 'delete_selected']

    def make_inactive(self, request, queryset):
        '''Mark items as inactive'''
        queryset.update(status='inactive')
    make_inactive.short_description = 'Mark selected as inactive'

    def make_active(self, request, queryset):
        '''Mark items as active'''
        queryset.update(status='active')
    make_active.short_description = 'Mark selected as active'

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(owner=request.user)
        return qs
"""

    def generate_fastapi_admin(self) -> str:
        """Generate FastAPI admin panel (with Starlette admin)"""
        return f"""
from starlette_admin import BaseView, expose
from starlette_admin.contrib.sqlalchemy import ModelView
from sqlalchemy.orm import Session

class {self.model_name}AdminView(ModelView, model={self.model_name}):
    '''Admin interface for {self.model_name}'''
    name = '{self.model_name}'
    label = '{self.model_name}s'
    icon = 'fa fa-list'

    column_list = ['{self.model_name}.id', '{self.model_name}.name', '{self.model_name}.created_at']
    column_searchable_list = ['{self.model_name}.name']
    column_sortable_list = ['{self.model_name}.created_at']
    column_filters = ['{self.model_name}.created_at']

    form_columns = ['name', 'description']

    details_columns = ['id', 'name', 'description', 'created_at', 'updated_at']

    def is_accessible(self, request) -> bool:
        return request.user.is_staff

    async def on_model_change(self, data, model, is_created, request):
        '''Hook called on model change'''
        pass

    async def scaffold_form(self):
        '''Scaffold form fields'''
        pass
"""


def generate_admin_panel(framework: str, model_name: str) -> Dict[str, str]:
    """
    Generate admin panel code.

    Args:
        framework: django or fastapi
        model_name: e.g., "User"

    Returns: dict of {filename: code_content}
    """
    generator = AdminPanelGenerator(framework, model_name)
    output = {}

    if framework == "django":
        output["admin.py"] = generator.generate_django_admin()
    elif framework == "fastapi":
        output["admin.py"] = generator.generate_fastapi_admin()

    return output
