from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Event, Registration, Comment, UserFollow, UserPreferences
from django.core.validators import EmailValidator
from rest_framework.validators import UniqueValidator
from django.utils import timezone
from drf_yasg.utils import swagger_serializer_method

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        help_text="The username of the user attempting to log in."
    )
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'},
        help_text="The password of the user. This field is write-only."
    )


class TokenSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="The access token for authentication.")
    refresh = serializers.CharField(help_text="The refresh token for renewing access.")


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField(
        help_text="The total number of followers the user has."
    )
    following_count = serializers.SerializerMethodField(
        help_text="The total number of users the user is following."
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'bio', 'profile_picture', 
            'date_of_birth', 'location', 'followers_count', 
            'following_count', 'date_joined'
        ]
        read_only_fields = ['date_joined']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'help_text': 'The user password. This field is write-only.'
            },
            'email': {
                'required': True,
                'help_text': 'The user email address. Must be unique and is required.'
            },
            'profile_picture': {
                'help_text': 'URL of the user’s profile picture. Optional.'
            },
            'bio': {
                'help_text': 'Short biography or description of the user. Optional.'
            },
            'location': {
                'help_text': 'Current location of the user. Optional.'
            },
            'date_of_birth': {
                'help_text': 'User’s date of birth in YYYY-MM-DD format. Optional.'
            },
        }

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField)
    def get_followers_count(self, obj):
        return obj.followers.count()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField)
    def get_following_count(self, obj):
        return obj.following.count()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="The user password. This field is write-only and required."
    )
    profile_picture = serializers.ImageField(
        required=False,
        help_text="Optional profile picture of the user. Must be an image file."
    )
    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Optional date of birth in YYYY-MM-DD format."
    )
    phone_number = serializers.CharField(
        max_length=15,
        required=False,
        help_text="Optional phone number of the user. Maximum length is 15 characters."
    )
    location = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Optional location of the user. Maximum length is 100 characters."
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'bio', 'password', 'profile_picture', 
            'date_of_birth', 'phone_number', 'location', 'interests'
        ]
        extra_kwargs = {
            'password': {
                'write_only': True,
                'help_text': 'The user password. This field is write-only.'
            },
            'email': {
                'validators': [EmailValidator()],
                'help_text': 'A valid email address. Must be unique.'
            },
        }
        

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        extra_kwargs = {
            'id': {'help_text': 'Unique identifier for the category.'},
            'name': {'help_text': 'The name of the category.'},
            'description': {'help_text': 'A brief description of the category.'},
            'created_at': {'help_text': 'The timestamp when the category was created.'}
        }


class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'created_by']
        read_only_fields = ['created_at', 'created_by']
        extra_kwargs = {
            'name': {'help_text': 'The name of the category. This field is required.'},
            'description': {'help_text': 'A brief description of the category. This field is required.'},
        }

    def validate_name(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("The name field is required and cannot be empty.")
        return value

    def validate_description(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("The description field is required and cannot be empty.")
        return value


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField(read_only=True)
    author_id = serializers.IntegerField(
        source='author.id', 
        read_only=True,
        help_text="The ID of the author who created the comment."
    )


    class Meta:
        model = Comment
        fields = ['id', 'event', 'author_id', 'content', 'created_at', 
                    'updated_at', 'parent', 'replies', 'likes_count', 'replies_count']
        read_only_fields = ['created_at', 'updated_at', 'replies_count']
        extra_kwargs = {
            'event': {'help_text': 'The ID of the event this comment is associated with.'},
            'content': {'help_text': 'The text content of the comment.'},
            'parent': {'help_text': 'The ID of the parent comment if this comment is a reply.'},
        }

    @swagger_serializer_method(serializer_or_field=serializers.ListField(
        child=serializers.DictField(),
        help_text="A list of replies to this comment."
    ))
    def get_replies(self, obj):
        if obj.parent is None:  # Only get replies for parent comments
            replies = Comment.objects.filter(parent=obj)
            return CommentSerializer(replies, many=True).data
        return []

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField(
        help_text="The number of likes this comment has received."
    ))
    def get_likes_count(self, obj):
        return obj.likes.count()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField(
        help_text="The number of replies this comment has received."
    ))
    def get_replies_count(self, obj):
        return obj.replies.count() 


class CommentCreateSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    likes_count = serializers.SerializerMethodField(read_only=True)
    replies_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'event', 'content', 'parent', 'author',
            'created_at', 'updated_at', 'likes_count', 'replies_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'author']
        extra_kwargs = {
            'event': {'help_text': 'The ID of the event the comment belongs to.'},
            'content': {'help_text': 'The text content of the comment.'},
            'parent': {'help_text': 'The ID of the parent comment (if this is a reply).'}
        }

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField)
    def get_likes_count(self, obj):

        return obj.likes.count()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField)
    def get_replies_count(self, obj):
        return obj.replies.count()

    
class RegistrationSerializer(serializers.ModelSerializer):
    attendee = UserSerializer(read_only=True)
    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        help_text="The ID of the event the registration belongs to."
    )
    status = serializers.ChoiceField(
        choices=Registration.STATUS_CHOICES,
        help_text="The status of the registration (e.g., 'confirmed', 'cancelled')."
    )
    notes = serializers.CharField(
        required=False,
        help_text="Optional notes provided by the attendee."
    )

    class Meta:
        model = Registration
        fields = [
            'id', 'event', 'attendee', 'status', 
            'registration_date', 'cancelled_date', 'notes'
        ]
        read_only_fields = ['id', 'registration_date', 'cancelled_date', 'attendee']
        extra_kwargs = {
            'event': {'help_text': 'The event ID associated with this registration.'},
            'notes': {'help_text': 'Additional notes or comments about the registration.'},
        }


class RegistrationCreateSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        help_text="The ID of the event for which the registration is being created."
    )
    status = serializers.ChoiceField(
        choices=Registration.STATUS_CHOICES,
        help_text="The status of the registration (e.g., 'pending', 'confirmed')."
    )
    notes = serializers.CharField(
        required=False,
        help_text="Optional notes provided by the attendee during registration."
    )

    class Meta:
        model = Registration
        fields = ['event', 'status', 'notes']
        read_only_fields = ['id', 'registration_date', 'cancelled_date']
        extra_kwargs = {
            'event': {'help_text': 'The event ID associated with the registration.'},
            'notes': {'help_text': 'Additional information or comments about the registration.'}
        }


class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(
        read_only=True,
        help_text="Details of the user organizing the event."
    )
    category = CategorySerializer(
        read_only=True,
        help_text="Details of the event category."
    )
    comments_count = serializers.SerializerMethodField(
        help_text="Total number of comments associated with the event."
    )
    registrations_count = serializers.SerializerMethodField(
        help_text="Total number of confirmed registrations for the event."
    )
    is_favorited = serializers.SerializerMethodField(
        help_text="Indicates if the event is marked as favorite by the current user."
    )
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'organizer', 
            'category', 'location', 'venue', 'start_date', 'end_date',
            'capacity', 'price', 'image', 'status', 'is_private',
            'created_at', 'updated_at', 'comments_count', 
            'registrations_count', 'is_favorited'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField)
    def get_comments_count(self, obj):
        return obj.comments.count()

    @swagger_serializer_method(serializer_or_field=serializers.IntegerField)
    def get_registrations_count(self, obj):
        return obj.registrations.filter(status='confirmed').count()

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(id=request.user.id).exists()
        return False


class EventCreateSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(
        read_only=True, 
        help_text="Unique slug for the event, automatically generated."
    )
    organizer = serializers.PrimaryKeyRelatedField(
        read_only=True, 
        help_text="ID of the user who organizes the event."
    )
    comments_count = serializers.IntegerField(
        read_only=True, 
        help_text="Total number of comments associated with the event."
    )
    registrations_count = serializers.IntegerField(
        read_only=True, 
        help_text="Total number of users registered for the event."
    )
    is_favorited = serializers.BooleanField(
        read_only=True, 
        help_text="Indicates if the event is marked as a favorite by the current user."
    )
    created_at = serializers.DateTimeField(
        read_only=True, 
        help_text="Timestamp of when the event was created."
    )
    updated_at = serializers.DateTimeField(
        read_only=True, 
        help_text="Timestamp of when the event was last updated."
    )

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'organizer', 
            'category', 'location', 'venue', 'start_date', 'end_date',
            'capacity', 'price', 'image', 'status', 'is_private',
            'created_at', 'updated_at', 'comments_count', 
            'registrations_count', 'is_favorited'
        ]
        extra_kwargs = {
            'title': {'help_text': 'The title of the event. This field is required.'},
            'description': {'help_text': 'A detailed description of the event.'},
            'category': {'help_text': 'The category ID to which the event belongs.'},
            'location': {'help_text': 'The geographical location of the event.'},
            'venue': {'help_text': 'The venue or specific address where the event will be held.'},
            'start_date': {'help_text': 'The start date and time of the event in YYYY-MM-DD HH:MM format.'},
            'end_date': {'help_text': 'The end date and time of the event in YYYY-MM-DD HH:MM format.'},
            'capacity': {'help_text': 'The maximum number of attendees allowed for the event.'},
            'price': {'help_text': 'The cost of attending the event. Enter 0 for free events.'},
            'image': {'help_text': 'A URL or file path to the event image.'},
            'status': {'help_text': 'The status of the event (e.g., "active", "cancelled").'},
            'is_private': {'help_text': 'Boolean indicating if the event is private (only accessible by invite).'},
        }
    

class EventDetailSerializer(EventSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    registrations = RegistrationSerializer(many=True, read_only=True)
    
    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ['comments', 'registrations']


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = ['notification_preference', 'email_notifications', 
                 'push_notifications', 'private_profile']


class UserFollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = UserFollow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['created_at']
