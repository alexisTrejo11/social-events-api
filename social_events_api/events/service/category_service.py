# services.py
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from ..models import Category
from django.db.models import QuerySet


User = get_user_model()

class CategoryService:
    VALID_SORT_FIELDS = {
        'name': ('name', '-name'),
        'created_at': ('created_at', '-created_at'),
    }
    
    DEFAULT_SORT = '-created_at'  # Default sorting
    DEFAULT_PAGE_SIZE = 10

    @staticmethod
    def create_category(data: Dict[Any, Any], user: User) -> Category:
        category = Category.objects.create(
            **data,
            created_by=user
        )
        return category

    @staticmethod
    def update_category(instance: Category, data: Dict[Any, Any], user: User) -> Category:
        CategoryService._validate_user_authority(instance, user)
        
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    @staticmethod
    def delete_category(instance: Category, user: User) -> None:
        CategoryService._validate_user_authority(instance, user)
        instance.delete()


    def _validate_user_authority(category: Category, user: User):
        if category.created_by != user:
            raise PermissionError("You do not have permission to delete this category.")
        

    @classmethod
    def get_sorted_categories(
        cls,
        sort_by: Optional[str] = None,
        sort_direction: Optional[str] = None,
        search_query: Optional[str] = None) -> QuerySet:
        
        all_categories = Category.objects.all()

        if search_query:
            all_categories = all_categories.filter(name__icontains=search_query)

        # Determine sort field
        sort_field = cls.DEFAULT_SORT
        if sort_by and sort_by in cls.VALID_SORT_FIELDS:
            if sort_direction and sort_direction.lower() == 'asc':
                sort_field = cls.VALID_SORT_FIELDS[sort_by][0]  
            else:
                sort_field = cls.VALID_SORT_FIELDS[sort_by][1] 

        return all_categories.order_by(sort_field)

