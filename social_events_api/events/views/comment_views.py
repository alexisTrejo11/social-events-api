from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import Comment, Event
from ..serializers import CommentCreateSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentCreateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Filter comments by event if event_id is provided"""
        queryset = Comment.objects.all()
        event_id = self.request.query_params.get('event', None)
        if event_id:
            queryset = queryset.filter(event_id=event_id, parent=None)
        return queryset

    def perform_create(self, serializer):
        """Set the author as the current user"""
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        """Only allow users to edit their own comments"""
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "You do not have permission to edit this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Only allow users to delete their own comments"""
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Toggle like status of a comment"""
        comment = self.get_object()
        user = request.user
        
        if comment.likes.filter(id=user.id).exists():
            comment.likes.remove(user)
            return Response({
                'status': 'unliked',
                'likes_count': comment.likes.count()
            })
        else:
            comment.likes.add(user)
            return Response({
                'status': 'liked',
                'likes_count': comment.likes.count()
            })

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get all replies for a comment"""
        comment = self.get_object()
        replies = comment.replies.all()
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)