from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from ..serializers import CommentCreateSerializer, CommentSerializer
from ..service.comment_service import CommentService
from ..service.event_query_service import EventQueryService
from ..models import Comment
from ..utils.swagger_examples import _COMMENT_EXAMPLE, _COMMENT_LIST_EXAMPLE, COMMENT_ERROR_EXAMPLES as _ERROR_EXAMPLES

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    comment_service = CommentService()
    event_service = EventQueryService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CommentCreateSerializer
        return super().get_serializer_class()

    @swagger_auto_schema(
        operation_description="Create a new comment (authenticated users only)",
        request_body=CommentCreateSerializer,
        responses={
            201: openapi.Response(
                description="Comment created successfully",
                examples={'application/json': _COMMENT_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            ),
            403: openapi.Response(
                description="Authorization error",
                examples={'application/json': _ERROR_EXAMPLES['FORBIDDEN_ERROR']}
            )
        },
        tags=['Comment']
    )
    def create(self, request):
        """Create a new comment with validated data."""
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.comment_service.validate_create(serializer.validated_data)
        if not validation.success:
            return Response(
                data={'detail': validation.error_message},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = self.comment_service.create(serializer.validated_data, user)
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="Update comment (author only)",
        request_body=CommentSerializer,
        responses={
            200: openapi.Response(
                description="Comment updated successfully",
                examples={'application/json': _COMMENT_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            ),
            403: openapi.Response(
                description="Authorization error",
                examples={'application/json': _ERROR_EXAMPLES['FORBIDDEN_ERROR']}
            )
        },
        tags=['Comment']
    )
    def update(self, request, *args, **kwargs):
        """Update an existing comment with authorization check."""
        instance = self.get_object()
        self.comment_service.validate_authority(instance, request.user)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete comment (author only)",
        responses={
            204: openapi.Response(description="Comment deleted successfully"),
            403: openapi.Response(
                description="Authorization error",
                examples={'application/json': _ERROR_EXAMPLES['FORBIDDEN_ERROR']}
            )
        },
        tags=['Comment']
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a comment with authorization check."""
        instance = self.get_object()
        self.comment_service.validate_authority(instance, request.user)
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Like a comment (authenticated users only)",
        responses={
            200: openapi.Response(
                description="Like registered successfully",
                examples={'application/json': {'detail': 'Like successfully registered'}}
            ),
            400: openapi.Response(
                description="Like processing error",
                examples={'application/json': _ERROR_EXAMPLES['LIKE_ERROR']}
            )
        },
        tags=['Comment']
    )
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Handle comment liking functionality."""
        comment = self.get_object()
        user = request.user
        message = self.comment_service.like(comment, user)
        return Response(
            data={'detail': message},
            status=status.HTTP_200_OK if 'success' in message.lower() else status.HTTP_400_BAD_REQUEST
        )

    @swagger_auto_schema(
        operation_description="Get comments by event ID",
        manual_parameters=[
            openapi.Parameter(
                'eventId', openapi.IN_PATH,
                description="ID of the event",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="Comments retrieved successfully",
                examples={'application/json': _COMMENT_LIST_EXAMPLE}
            ),
            404: openapi.Response(
                description="Event not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Comment']
    )
    @action(detail=False, methods=['get'], url_path='eventId/(?P<eventId>\d+)')
    def get_by_event_id(self, request, eventId):
        """Retrieve comments associated with a specific event."""
        event = self.event_service.get_event_by_id_or_slug(eventId)
        if not event:
            return Response(
                data={'detail': 'Event not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        comments = self.comment_service.get_by_event(event)
        return Response(
            CommentSerializer(comments, many=True).data,
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="Get comment replies",
        responses={
            200: openapi.Response(
                description="Replies retrieved successfully",
                examples={'application/json': _COMMENT_LIST_EXAMPLE}
            )
        },
        tags=['Comment']
    )
    @action(detail=True, methods=['get'])
    def replies(self, request, pk):
        """Retrieve replies to a specific comment."""
        comment = self.get_object()
        replies = self.comment_service.get_replies(comment)
        return Response(
            self.get_serializer(replies, many=True).data,
            status=status.HTTP_200_OK
        )