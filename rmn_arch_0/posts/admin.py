from django.contrib import admin
from .models import (
    Post,
    PostImage,
    Comment,
    Rating,
    Report,
)


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = [
        'uuid',
        'user',
        'image_count',
        'rating_count',
        'comment_count',
        'report_count',
        'anonymous',
        'reportable',
        'show',
        'created',
        ]
    list_filter = ['anonymous', 'reportable', 'show',]
    readonly_fields = ['user']
    search_fields = ['uuid',]
    inlines = [PostImageInline,]


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    readonly_fields = ['post',]
    search_fields = ['post__uuid',]


class PostRelatedAdmin(admin.ModelAdmin):
    readonly_fields = ['post', 'user']
    search_fields = ['post__uuid',]


@admin.register(Report)
class ReportAdmin(PostRelatedAdmin):
    date_hierarchy = 'created'
    list_display = ['post_uuid', 'user', 'reason', 'created', 'modified',]
    list_filter = ['reason',]

    @admin.display(description='Post')
    def post_uuid(self, obj):
        return obj.post.uuid


@admin.register(Rating)
class RatingAdmin(PostRelatedAdmin):
    list_display = ['post', 'user', 'session_key', 'rate', 'created',]
    list_filter = ['rate',]


admin.site.register(Comment, PostRelatedAdmin)
