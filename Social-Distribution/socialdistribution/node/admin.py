from django.contrib import admin
from .models import Author, Like, Comment, Post, Follow, Repost, SiteSetting, RemoteNode, AllowedNode
from solo.admin import SingletonModelAdmin

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
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_active=True)
    
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