from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ..models import Category
from ..serializers import CategorySerializer, CategoryCreateSerializer
from ..service.category_service import CategoryService
from rest_framework.pagination import PageNumberPagination

class CategoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    category_service = CategoryService
    pagination_class = CategoryPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'create':
            return CategoryCreateSerializer
        return CategorySerializer
    

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    

    def list(self, request, *args, **kwargs):
        """
        List categories with optional sorting and searching
        
        Query Parameters:
            sort_by: Field to sort by ('name' or 'created_at')
            sort_direction: 'asc' or 'desc'
            search: Search term for filtering by name
            page: Page number for pagination
            page_size: Number of items per page
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
    
    
    @action(detail=True, methods=['get'])
    def get_by_id(self, request, pk=None):
        category = get_object_or_404(Category, pk=pk)
        serializer = self.get_serializer(category)
        return Response(serializer.data)


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
    
        new_category = self.category_service.create_category(
            data=serializer.validated_data, 
            user=request.user
        )

        new_category = self.get_serializer(new_category).data
        return Response(new_category, status=status.HTTP_201_CREATED)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()  

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        category_updated = self.category_service.update_category(
                instance=instance,
                data=serializer.validated_data,
                user=request.user
            )        
        
        category_updated = self.get_serializer(category_updated).data
        return Response(category_updated)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        self.category_service.delete_category(instance, request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)
