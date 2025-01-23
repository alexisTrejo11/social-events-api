from ..utils.result import Result
from django.utils import timezone
from ..models import Event
from django.utils.text import slugify


class EventValidationService:
    def validate(self, data,  is_creation: bool):
        date_result = self.__validate_event_date(data)
        if not date_result.success:
            return date_result

        image_result = self.__validate_image(data)
        if not image_result.success:
            return image_result

        status_result =  self.__validate_status(data)
        if not status_result.success:
            return status_result
        
        slug_result = self.__validate_slug(data, is_creation)
        if not slug_result.success:
            return slug_result

        return Result.success()
    
    def __validate_event_date(self, data) -> Result:
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] < timezone.now():
                return Result.failure("Event cannot start in the past")
            
            if data['end_date'] <= data['start_date']:
                return Result.failure("End date must be after start date")
            
        return Result.success()
            
    def __validate_image(self, data):
        if 'image' in data:
            image = data['image']
            if hasattr(image, 'size'):
                if image.size > 5 * 1024 * 1024:  # 5MB limit
                    return Result.failure("Image file too large. Size should not exceed 5 MB.")

                if not image.content_type.startswith('image/'):
                    return Result.failure("Uploaded file is not a valid image.")
        return Result.success()
    
    def __validate_status(self, data):
        if 'status' in data and data['status'] not in ['draft', 'published', 'cancelled']:
            return Result.failure("Invalid status value")
        return Result.success()
    
    def __validate_slug(self, data, is_creation: bool):
        title = data.get('title')
        if not title:
            return Result.failure("Title is required to generate a slug")

        slug = slugify(title)

        if is_creation:
            if Event.objects.filter(slug=slug).exists():
                return Result.failure("Name must be unique. The provided name already exists.")
        else:
            event_id = data.get('id')  
            if event_id:
                if Event.objects.filter(slug=slug).exclude(id=event_id).exists():
                    return Result.failure("Name must be unique. The provided name already exists.")
            else:
                return Result.failure("Event ID is required for updating")

        data['slug'] = slug
        return Result.success()
    
    