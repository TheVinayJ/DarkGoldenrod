from django.contrib import admin, messages
from .models import Author, Like, Comment, Post, Follow, Repost, SiteSetting, RemoteNode, AllowedNode
from solo.admin import SingletonModelAdmin
from django.urls import path
from django.shortcuts import render, redirect

class AuthorAdmin(admin.ModelAdmin):
    # Display specific fields in the list view
    list_display = ('display_name', 'email', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('display_name', 'email')
    actions = ['approve_users']

    # Action to approve selected users
    def approve_users(self, request, queryset):
        # Only approve users who are currently inactive
        updated_count = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f"{updated_count} user(s) have been approved.")
    approve_users.short_description = "Approve selected users"

    # Customize the list display to show pending (inactive) users
    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     return qs.filter(is_active=True)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('inactive-users/', self.admin_site.admin_view(self.inactive_users_view), name='inactive-users'),
        ]
        return custom_urls + urls

    def inactive_users_view(self, request):
        # Get all inactive authors
        inactive_users = Author.objects.filter(is_active=False)

        if request.method == 'POST':
            selected_ids = request.POST.getlist('user_ids')
            if selected_ids:
                updated_count = Author.objects.filter(id__in=selected_ids).update(is_active=True)
                messages.success(request, f"{updated_count} user(s) have been approved.")
                return redirect('admin:inactive-users')

        return render(request, 'admin/inactive_users.html', {'inactive_users': inactive_users})
    
# Register your models here.
admin.site.register(Author, AuthorAdmin)
# admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Post)
admin.site.register(Follow)
admin.site.register(Repost)
admin.site.register(SiteSetting, SingletonModelAdmin)

@admin.register(AllowedNode)
class AllowedNodeAdmin(admin.ModelAdmin):
    list_display = ('url', 'username', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('url', 'username')
    actions = ['activate_nodes', 'deactivate_nodes']

    def activate_nodes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} node(s) activated.")
    activate_nodes.short_description = "Activate selected nodes"

    def deactivate_nodes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} node(s) deactivated.")
    deactivate_nodes.short_description = "Deactivate selected nodes"


@admin.register(RemoteNode)
class RemoteNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'url')
    actions = ['activate_nodes', 'deactivate_nodes']

    def activate_nodes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} node(s) activated.")
    activate_nodes.short_description = "Activate selected nodes"

    def deactivate_nodes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} node(s) deactivated.")
    deactivate_nodes.short_description = "Deactivate selected nodes"