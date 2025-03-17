from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import PageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeGetSerializer, RecipePostSerializer,
                             ShoppingCartSerializer, SubscriptionSerializer,
                             SubscriptionsListSerializer, TagSerializer)
from api.utils import (create_related_object, delete_related_object,
                       get_pdf_shopping_list)
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeGetSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipePostSerializer
        return RecipeGetSerializer

    def get_queryset(self):
        queryset = Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags',
            'ingredients'
        )
        return (queryset.get_recipe_extra_obj(self.request.user)
                if self.request.user.is_authenticated else queryset)

    @action(methods=('post',), detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return create_related_object(pk, request, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk):
        return delete_related_object(pk, request, ShoppingCart)

    @action(detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientRecipe.objects.filter(
                recipe__shoppingcarts__user=request.user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit'
            ).annotate(
                ingredient_amount=Sum('amount')
            ).order_by(
                'ingredient__name'
            )
        )
        return get_pdf_shopping_list(ingredients)

    @action(methods=('post',), detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return create_related_object(pk, request, FavoriteSerializer)

    @favorite.mapping.delete
    def unmake_recipe_favorite(self, request, pk):
        return delete_related_object(pk, request, Favorite)


class UserViewSet(UserViewSet):
    pagination_class = PageNumberPagination

    def get_permissions(self):
        return ((IsAuthenticated(),) if self.action == 'me'
                else super().get_permissions())

    @action(detail=False,
            permission_classes=(IsAuthenticated,),
            serializer_class=SubscriptionsListSerializer)
    def subscriptions(self, request):
        queryset = self.filter_queryset(
            User.objects.filter(following__user=self.request.user)
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, permission_classes=(IsAuthenticated,),
            methods=('post',))
    def subscribe(self, request, id):
        get_object_or_404(User, id=id)
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        get_object_or_404(User, id=id)
        to_delete = Subscription.objects.filter(
            user=request.user, author=id
        ).delete()
        if to_delete[0] == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'message': 'Объект не найден'})
        return Response(status=status.HTTP_204_NO_CONTENT)
