from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from rest_framework.authtoken.admin import TokenProxy

from .models import (Ingredient, IngredientRecipe, Recipe, ShoppingCart, Tag,
                     TagRecipe)

admin.site.empty_value_display = 'Не найдено'
admin.site.unregister(TokenProxy)
admin.site.unregister(Group)


class RecipeIngredientInline(admin.TabularInline):
    model = IngredientRecipe
    min_num = 1


class TagRecipeInLine(admin.TabularInline):
    model = TagRecipe
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline, TagRecipeInLine)
    list_display = ('name', 'get_favorites', 'author',
                    'get_tags', 'get_ingredients', 'get_image', 'id')
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name', 'author')

    @admin.display(description='Избранное')
    def get_favorites(self, obj):
        return obj.favorites.count()

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return (', '.join
                ([ingredient.name for ingredient in obj.ingredients.all()]))

    @admin.display(description='Изображение блюда')
    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="100" height="80">')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'id')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount', 'id')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe', 'ingredient')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'id')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug', 'id')
    list_filter = ('name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')


@admin.register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tag', 'id')
    list_filter = ('recipe', 'tag')
    search_fields = ('recipe', 'tag')
