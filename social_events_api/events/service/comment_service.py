from ..models import Comment, User, Event
from django.core.exceptions import ValidationError
from ..utils.result import Result

class CommentService:
    def validate_authority(self, comment : Comment, user: User):
        if comment.author != user:
                raise ValidationError("You do not have permission to edit this comment.")
        
    def get_by_event(self, event: Event):
         return Comment.objects.filter(event=event)
    
    def get_replies(self, comment: Event):
        return comment.replies.all()

    def like(self, comment, user) -> dict:
        if comment.likes.filter(id=user.id).exists():
            comment.likes.remove(user)
            return {'status': 'unlike', 'likes_count': comment.likes.count()}
        else:
            comment.likes.add(user)
            return {'status': 'like', 'likes_count': comment.likes.count()}
    
    def create(self, data, user):      
        data['author'] = user
        return Comment.objects.create(**data)

    def validate_create(self, data):
        self.__validate_parent(data)
        
        content = data.get('content')

        if len(content) < 1:
            return Result.failure("Comment content cannot be empty")
        if len(content) > 1000:
            return Result.failure("Comment is too long (max 1000 characters)")
        return Result.success()

    def __validate_parent(self, data):
        parent = data.get('parent')
        event = data.get('event')

        if parent:
            if parent.parent:
                raise ValidationError("Nested replies are not allowed (max 1 level)")
            if parent.event != event:
                raise ValidationError("Reply must be to a comment on the same event")


    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_replies_count(self, obj):
        return obj.replies.count()

    