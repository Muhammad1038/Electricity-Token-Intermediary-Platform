from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    ordering = ("-created_at",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("user", "message_count", "created_at", "updated_at")
    readonly_fields = ("id", "user", "created_at", "updated_at")
    inlines = [MessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("short_content", "role", "conversation", "created_at")
    list_filter = ("role",)
    readonly_fields = ("id", "conversation", "role", "content", "created_at")

    def short_content(self, obj):
        return obj.content[:80] + ("..." if len(obj.content) > 80 else "")
    short_content.short_description = "Content"
