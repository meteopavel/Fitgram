from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Exists, OuterRef

User = get_user_model()

MAX_TAG_NAME_LENGTH = 256
MAX_INGREDIENT_NAME_LENGTH = 256
MAX_RECIPE_NAME_LENGTH = 200
MAX_MEASUREMENT_UNIT_LENGTH = 50


class RecipeQuerySet(models.QuerySet):
    def get_recipe_extra_obj(self, user):
        return self.annotate(
            is_favorited=Exists(user.favorites.filter(
                recipe__id=OuterRef('id')
            )),
            is_in_shopping_cart=Exists(user.shoppingcarts.filter(
                recipe__id=OuterRef('id')
            ))
        ).order_by('-pub_date')


class UserRecipeBaseModel(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        default_related_name = '%(class)ss'
        constraints = (
            models.UniqueConstraint(
                name='%(app_label)s_%(class)s already exists',
                fields=('user', 'recipe'),
            ),
        )
        abstract = True


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_TAG_NAME_LENGTH,
        unique=True,
        verbose_name='Название тега'
    )
    color = ColorField(
        unique=True,
        verbose_name='Цвет тега'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug тега'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME_LENGTH,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единицы измерения'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='%(app_label)s_%(class)s already exists',
            )
        ]
        ordering = ('name',)


class Recipe(models.Model):
    pub_date = models.DateTimeField('Дата', auto_now_add=True)
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe'
    )
    author = models.ForeignKey(
        User, related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe'
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH,
        unique=True,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение блюда'
    )
    text = models.TextField(
        verbose_name='Текст рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MaxValueValidator(32767, 'Количество не может быть выше 32767'),
            MinValueValidator(1, 'Количество не может быть ниже 1')),
        verbose_name='Время приготовления'
    )

    objects = RecipeQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Favorite(UserRecipeBaseModel):
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Списки избранного'

    def __str__(self):
        return f'{self.user.username} {self.recipe.name}'


class ShoppingCart(UserRecipeBaseModel):
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user.username} {self.recipe.name} '


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, related_name='ingredients_recipe',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            MaxValueValidator(32767, 'Количество не может быть выше 32767'),
            MinValueValidator(1, 'Количество не может быть ниже 1'))
    )

    class Meta:
        verbose_name = 'Ингредиент к рецепту'
        verbose_name_plural = 'Ингредиенты к рецептам'

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Тег к рецепту'
        verbose_name_plural = 'Теги к рецептам'

    def __str__(self):
        return f'{self.tag} {self.recipe}'
