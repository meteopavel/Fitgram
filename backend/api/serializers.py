import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.transaction import atomic
from djoser.serializers import UserSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (BooleanField, CurrentUserDefault,
                                        HiddenField, ImageField,
                                        ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField)
from rest_framework.validators import UniqueTogetherValidator

from api.validators import validate_empty_fields, validate_list
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeGetSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')
    name = ReadOnlyField(source='ingredient.name')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientRecipePostSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(source='ingredient.id',
                                queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeGetSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeGetSerializer(source='ingredients_recipe',
                                                many=True)
    image = Base64ImageField(required=False, allow_null=True)
    is_in_shopping_cart = BooleanField(default=0)
    is_favorited = BooleanField(default=0)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')


class RecipePostSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(many=True,
                                  queryset=Tag.objects.all())
    author = HiddenField(default=CurrentUserDefault())
    ingredients = IngredientRecipePostSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ('author',)

    def validate_tags(self, value):
        validate_list(value, 'теги')
        return value

    def validate_ingredients(self, value):
        ingredients = [
            (value[i]['ingredient'])['id'] for i in range(len(value))
        ]
        validate_list(ingredients, 'ингредиенты')
        return value

    def create_ingredients(self, recipe, ingredients):
        ingredients_recipe = [IngredientRecipe(
            recipe=recipe,
            ingredient=(ingredient.get('ingredient'))['id'],
            amount=ingredient.get('amount')
        ) for ingredient in ingredients]
        IngredientRecipe.objects.bulk_create(ingredients_recipe)

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        validate_empty_fields(validated_data)
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeGetSerializer(instance,
                                   context=self.context).data


class RecipeMiniSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsListSerializer(UserSerializer):
    recipes = SerializerMethodField(method_name='get_recipes')
    recipes_count = ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMiniSerializer(recipes, many=True,
                                    context=self.context).data


class SubscriptionSerializer(ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('author', 'user')

        validators = (UniqueTogetherValidator(
            queryset=Subscription.objects.all(),
            fields=('user', 'author'),
            message='Вы уже подписались на этого автора ранее'),)

    def validate_author(self, obj):
        if obj == self.context.get('request').user:
            raise ValidationError('Нельзя подписаться на себя')
        return obj

    def to_representation(self, instance):
        return SubscriptionsListSerializer(instance.author,
                                           context=self.context).data


class FavoriteCartsBaseSerializer(ModelSerializer):
    class Meta:
        fields = ('recipe', 'user')

    def to_representation(self, instance):
        return RecipeMiniSerializer(
            instance.recipe,
            context=self.context
        ).data

    def validate(self, data):
        if self.Meta.model.objects.filter(
                user=self.context.get('request').user,
                recipe=data.get('recipe')).exists():
            raise ValidationError(
                f'Рецепт уже добавлен в'
                f' {self.Meta.model._meta.verbose_name.lower()}'
            )
        return data


class FavoriteSerializer(FavoriteCartsBaseSerializer):
    class Meta(FavoriteCartsBaseSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(FavoriteCartsBaseSerializer):
    class Meta(FavoriteCartsBaseSerializer.Meta):
        model = ShoppingCart


class UserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')
