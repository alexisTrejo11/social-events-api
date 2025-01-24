from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Event, Registration, Comment, UserFollow, UserPreferences
from django.core.validators import EmailValidator
from rest_framework.validators import UniqueValidator
from django.utils import timezone

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

class TokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'bio', 'profile_picture', 
                 'date_of_birth', 'location', 'followers_count', 
                 'following_count', 'date_joined']
        read_only_fields = ['date_joined']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    profile_picture = serializers.ImageField(required=False)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    phone_number = serializers.CharField(max_length=15, required=False)
    location = serializers.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'bio', 'password', 'profile_picture', 
            'date_of_birth', 'phone_number', 'location', 'interests'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'validators': [EmailValidator()]},
        }
        

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']

class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'created_by']
        read_only_fields = ['created_at', 'created_by']

    def validate_name(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("The name field is required and cannot be empty.")
        return value

    def validate_description(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("The description field is required and cannot be empty.")
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'event', 'author', 'content', 'created_at', 
                 'updated_at', 'parent', 'replies', 'likes_count', 'replies_count']
        read_only_fields = ['created_at', 'updated_at','replies_count']

    def get_replies(self, obj):
        if obj.parent is None:  # Only get replies for parent comments
            replies = Comment.objects.filter(parent=obj)
            return CommentSerializer(replies, many=True).data
        return []

    def get_likes_count(self, obj):
        return obj.likes.count()
    
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

    def validate_parent(self, value):
        if value:
            if value.parent:
                raise serializers.ValidationError("Nested replies are not allowed (max 1 level)")
            if value.event_id != self.initial_data.get('event'):
                raise serializers.ValidationError("Reply must be to a comment on the same event")
        return value
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_replies_count(self, obj):
        return obj.replies.count()
    

class RegistrationSerializer(serializers.ModelSerializer):
    attendee = UserSerializer(read_only=True)
    
    class Meta:
        model = Registration
        fields = ['id', 'event', 'attendee', 'status', 'registration_date', 
                 'cancelled_date', 'notes']
        read_only_fields = ['registration_date', 'cancelled_date']


class RegistrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ['event', 'status', 'notes']
        read_only_fields = ['id', 'registration_date', 'cancelled_date']


class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    registrations_count = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'slug', 'description', 'organizer', 
                 'category', 'location', 'venue', 'start_date', 'end_date',
                 'capacity', 'price', 'image', 'status', 'is_private',
                 'created_at', 'updated_at', 'comments_count', 
                 'registrations_count', 'is_favorited']
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_registrations_count(self, obj):
        return obj.registrations.filter(status='confirmed').count()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(id=request.user.id).exists()
        return False

class EventCreateSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)
    organizer = serializers.PrimaryKeyRelatedField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    registrations_count = serializers.IntegerField(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'organizer', 
            'category', 'location', 'venue', 'start_date', 'end_date',
            'capacity', 'price', 'image', 'status', 'is_private',
            'created_at', 'updated_at', 'comments_count', 
            'registrations_count', 'is_favorited'
        ]

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long")
        return value.strip()

    def validate_description(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Description must be at least 20 characters long")
        return value.strip()

    def validate_capacity(self, value):
        if value < 1:
            raise serializers.ValidationError("Capacity must be at least 1")
        if value > 10000:  # maximum capacity
            raise serializers.ValidationError("Capacity cannot exceed 10,000")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value

    def validate(self, data):
        # Validate start_date and end_date
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] < timezone.now():
                raise serializers.ValidationError({
                    "start_date": "Event cannot start in the past"
                })
            
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError({
                    "end_date": "End date must be after start date"
                })

        # Validate image file size and type
        if 'image' in data:
            image = data['image']
            if hasattr(image, 'size'):
                if image.size > 5 * 1024 * 1024:  # 5MB limit
                    raise serializers.ValidationError({
                        "image": "Image file too large. Size should not exceed 5 MB."
                    })
                
                if not image.content_type.startswith('image/'):
                    raise serializers.ValidationError({
                        "image": "Uploaded file is not a valid image."
                    })

        # Validate status
        if 'status' in data and data['status'] not in ['draft', 'published', 'cancelled']:
            raise serializers.ValidationError({
                "status": "Invalid status value"
            })

        return data

    def create(self, validated_data):
        # Set the organizer as the current user
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)
    

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
