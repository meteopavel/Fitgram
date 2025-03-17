from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'get_recipes', 'get_subscribers', 'id')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email')

    @admin.display(description='Рецепты')
    def get_recipes(self, obj):
        return obj.recipes.count()

    @admin.display(description='Подписчики')
    def get_subscribers(self, obj):
        return obj.following.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'id')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
