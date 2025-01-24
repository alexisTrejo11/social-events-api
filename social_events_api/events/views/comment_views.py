from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
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
        """Returns the appropriate serializer based on the action."""
        if self.action == 'create': 
            return CommentCreateSerializer
        return super().get_serializer_class()

    @swagger_auto_schema(
        operation_description="Create a new comment. Only authenticated users can create comments.",
        request_body=CommentCreateSerializer,
        responses={
            201: openapi.Response(
                description="Comment successfully created",
                examples={
                    'application/json': {
                        'id': 1,
                        'text': 'This is a comment',
                        'author': 'user1',
                        'created_at': '2025-01-24T14:22:00Z'
                    }
                }
            ),
            404: openapi.Response(
                description="Failed to validate the comment creation",
                examples={
                    'application/json': {'error': 'Error creating the comment'}
                }
            )
        },
        tags=['Comment']
    )
    def create(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.comment_service.validate_create(serializer.validated_data)
        if not validation.success:
            return Response(data=validation.error_message, status=status.HTTP_404_NOT_FOUND)

        comment = self.comment_service.create(serializer.validated_data, user)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update an existing comment. Only the author can update their comment.",
        request_body=CommentSerializer,
        responses={
            200: openapi.Response(
                description="Comment successfully updated",
                examples={
                    'application/json': {
                        'id': 1,
                        'text': 'Updated comment text',
                        'author': 'user1',
                        'created_at': '2025-01-24T14:22:00Z'
                    }
                }
            ),
            400: openapi.Response(
                description="Error updating the comment",
                examples={
                    'application/json': {'error': 'Not authorized to update this comment'}
                }
            )
        },
        tags=['Comment']
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.comment_service.validate_authority(instance, request.user)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an existing comment. Only the author can delete their comment.",
        responses={
            200: openapi.Response(
                description="Comment successfully deleted",
                examples={
                    'application/json': {'message': 'Comment successfully deleted'}
                }
            ),
            400: openapi.Response(
                description="Error deleting the comment",
                examples={
                    'application/json': {'error': 'Not authorized to delete this comment'}
                }
            )
        },
        tags=['Comment']
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.comment_service.validate_authority(instance, request.user)
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Like a comment. Authenticated users can like a comment.",
        responses={
            200: openapi.Response(
                description="Like successfully registered",
                examples={
                    'application/json': {'message': 'Like successfully registered'}
                }
            ),
            400: openapi.Response(
                description="Error registering the like",
                examples={
                    'application/json': {'error': 'Error registering the like'}
                }
            )
        },
        tags=['Comment']
    )
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        user = request.user
        message = self.comment_service.like(comment, user)
        return Response(data=message, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get comments by event ID.",
        responses={
            200: openapi.Response(
                description="Comments successfully fetched",
                examples={
                    'application/json': [
                        {
                            'id': 1,
                            'text': 'Comment on the event',
                            'author': 'user1',
                            'created_at': '2025-01-24T14:22:00Z'
                        }
                    ]
                }
            ),
            404: openapi.Response(
                description="Event not found",
                examples={
                    'application/json': {'error': 'Event not found'}
                }
            )
        },
        tags=['Comment']
    )
    @action(detail=False, methods=['get'], url_path='eventId/(?P<eventId>\d+)')
    def get_by_event_id(self, request, eventId):
        event = self.event_service.get_event_by_id_or_slug(eventId)
        if not event:
            return Response(data="Event not found", status=status.HTTP_404_NOT_FOUND)

        comments = self.comment_service.get_by_event(event)
        comments = CommentSerializer(comments, many=True).data
        return Response(data=comments, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get replies to a specific comment.",
        responses={
            200: openapi.Response(
                description="Replies successfully fetched",
                examples={
                    'application/json': [
                        {
                            'id': 2,
                            'text': 'Reply to the comment',
                            'author': 'user2',
                            'created_at': '2025-01-24T14:40:00Z'
                        }
                    ]
                }
            )
        },
        tags=['Comment']
    )
    @action(detail=True, methods=['get'])
    def replies(self, request, pk):
        comment = self.get_object()
        replies = self.comment_service.get_replies(comment)
        replies = self.get_serializer(replies, many=True)
        return Response(replies.data)
