from django.core.exceptions import ValidationError
from django.db import transaction
from ..models import Comment, User, Event
from ..utils.result import Result

class CommentService:
    def validate_authority(self, comment: Comment, user: User):
        if comment.author != user:
            raise ValidationError("You do not have permission to modify this comment.")
    
    def get_by_event(self, event: Event):
        return Comment.objects.filter(event=event).prefetch_related('author', 'likes')
    
    def get_replies(self, comment: Comment):
        return comment.replies.select_related('author').prefetch_related('likes')

    @transaction.atomic
    def like(self, comment: Comment, user: User) -> dict:
        if comment.likes.filter(id=user.id).exists():
            comment.likes.remove(user)
            status = 'unlike'
        else:
            comment.likes.add(user)
            status = 'like'
        
        return {
            'status': status, 
            'likes_count': comment.likes.count()
        }
    
    @transaction.atomic
    def create(self, data: dict, user: User) -> Comment:
        data['author'] = user
        return Comment.objects.create(**data)

    def validate_create(self, data: dict) -> Result:
        self.__validate_parent(data)
        
        content = data.get('content', '').strip()

        if not content:
            return Result.failure("Comment content cannot be empty")
        if len(content) > 1000:
            return Result.failure("Comment is too long (max 1000 characters)")
        
        return Result.success()

    def __validate_parent(self, data: dict):
        parent = data.get('parent')
        event = data.get('event')

        if parent:
            if parent.parent:
                raise ValidationError("Nested replies are not allowed (max 1 level)")
            if parent.event != event:
                raise ValidationError("Reply must be to a comment on the same event")

    def get_comment_metadata(self, comment: Comment) -> dict:
        return {
            'likes_count': comment.likes.count(),
            'replies_count': comment.replies.count()
        }

    @transaction.atomic
    def update(self, comment: Comment, data: dict, user: User) -> Comment:
        self.validate_authority(comment, user)
        
        for key, value in data.items():
            setattr(comment, key, value)
        
        comment.full_clean()
        comment.save()
        return comment

    @transaction.atomic
    def delete(self, comment: Comment, user: User):
        self.validate_authority(comment, user)
        comment.delete()