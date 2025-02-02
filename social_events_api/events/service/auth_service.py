from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.pagination import PageNumberPagination

from ..models import Category
from ..serializers import CategorySerializer, CategoryCreateSerializer
from ..service.category_service import CategoryService
from ..utils.swagger_examples import _CATEGORY_EXAMPLE, CATEGORY_ERROR_EXAMPLES as _ERROR_EXAMPLES

class CategoryPagination(PageNumberPagination):
    """
    Custom pagination class for Category endpoints.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Category operations:
    - List, retrieve, create, update, and delete categories.
    - Supports sorting, searching, and pagination.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CategoryPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    category_service = CategoryService()
   
    def get_serializer_class(self):
        """
        Returns the appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return CategoryCreateSerializer
        return CategorySerializer

    def get_permissions(self):
        """
        Returns the appropriate permissions based on the action.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_description="List all categories with optional sorting, searching, and pagination.",
        manual_parameters=[
            openapi.Parameter(
                'sort_by', openapi.IN_QUERY, description="Field to sort by ('name' or 'created_at')", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'sort_direction', openapi.IN_QUERY, description="Sort direction ('asc' or 'desc')", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'search', openapi.IN_QUERY, description="Search term for filtering by name", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY, description="Page number for pagination", type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY, description="Number of items per page", type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of categories",
                examples={
                    'application/json': [_CATEGORY_EXAMPLE]
                }
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """
        Endpoint to list categories with optional sorting, searching, and pagination.
        """
        sort_by = request.query_params.get('sort_by')
        sort_direction = request.query_params.get('sort_direction')
        search_query = request.query_params.get('search')

        queryset = self.category_service.get_sorted_categories(
            sort_by=sort_by,
            sort_direction=sort_direction,
            search_query=search_query
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Retrieve a category by its ID.",
        responses={
            200: openapi.Response(
                description="Category details",
                examples={
                    'application/json': _CATEGORY_EXAMPLE
                }
            ),
            404: openapi.Response(
                description="Category not found",
                examples={
                    'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']
                }
            )
        }
    )
    @action(detail=True, methods=['get'])
    def get_by_id(self, request, pk=None):
        """
        Endpoint to retrieve a specific category by its ID.
        """
        category = get_object_or_404(Category, pk=pk)
        serializer = self.get_serializer(category)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new category.",
        request_body=CategoryCreateSerializer,
        responses={
            201: openapi.Response(
                description="Category created successfully",
                examples={
                    'application/json': _CATEGORY_EXAMPLE
                }
            ),
            400: openapi.Response(
                description="Validation error",
                examples={
                    'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']
                }
            ),
            403: openapi.Response(
                description="Conflict error",
                examples={
                    'application/json': _ERROR_EXAMPLES['CONFLICT_ERROR']
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        """
        Endpoint to create a new category.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_category = self.category_service.create_category(
            data=serializer.validated_data,
            user=request.user
        )

        response_serializer = self.get_serializer(new_category)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update an existing category (full or partial).",
        request_body=CategoryCreateSerializer,
        responses={
            200: openapi.Response(
                description="Category updated successfully",
                examples={
                    'application/json': _CATEGORY_EXAMPLE
                }
            ),
            400: openapi.Response(
                description="Validation error",
                examples={
                    'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']
                }
            ),
            403: openapi.Response(
                description="Forbidden error",
                examples={
                    'application/json': _ERROR_EXAMPLES['FORBIDDEN_ERROR']
                }
            )
        }
    )
    def update(self, request, *args, **kwargs):
        """
        Endpoint to update an existing category.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        updated_category = self.category_service.update_category(
            instance=instance,
            data=serializer.validated_data,
            user=request.user
        )

        response_serializer = self.get_serializer(updated_category)
        return Response(response_serializer.data)

    @swagger_auto_schema(
        operation_description="Delete a category by its ID.",
        responses={
            204: openapi.Response(description="Category deleted successfully"),
            403: openapi.Response(
                description="Forbidden error",
                examples={
                    'application/json': _ERROR_EXAMPLES['FORBIDDEN_ERROR']
                }
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        """
        Endpoint to delete a category.
        """
        instance = self.get_object()
        self.category_service.delete_category(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)