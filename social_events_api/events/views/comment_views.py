from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from ..serializers import CommentCreateSerializer, CommentSerializer
from ..service.comment_service import CommentService
from ..service.event_query_service import EventQueryService
from ..models import Comment

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    comment_service = CommentService()
    event_service = EventQueryService()

    def get_serializer_class(self):
        if self.action == 'create': 
            return CommentCreateSerializer
        return super().get_serializer_class()
    
    def create(self, request):
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.comment_service.validate_create(serializer.validated_data)
        if not validation.success:
            return Response(data=validation.error_message, status=status.HTTP_404_NOT_FOUND)

        coment = self.comment_service.create(serializer.validated_data, user)

        CommentSerializer(coment).data
        return Response(status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        self.comment_service.validate_authority(instance, request.user)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.comment_service.validate_authority(instance, request.user)

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        user = request.user
        
        message = self.comment_service.like(comment, user)
        
        return Response(data=message, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path="/eventId/{pk}")
    def get_by_event_id(self, pk):
        event = self.event_service.get_event_by_id_or_slug(pk)
        if not event:
            Response(data="Event not found", status=status.HTTP_404_NOT_FOUND)

        comments = self.comment_service.get_by_event(event)

        comments = CommentSerializer(comments, many=True).data
        return Response(data=comments, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        comment = self.get_object()
        replies = self.comment_service.get_replies(comment)
        
        replies = self.get_serializer(replies, many=True)
        return Response(replies.data)