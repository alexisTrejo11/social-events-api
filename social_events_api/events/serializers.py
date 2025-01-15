# events/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Event, Registration, Comment, UserFollow, UserPreferences

User = get_user_model()

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

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'event', 'author', 'content', 'created_at', 
                 'updated_at', 'parent', 'replies', 'likes_count']
        read_only_fields = ['created_at', 'updated_at']

    def get_replies(self, obj):
        if obj.parent is None:  # Only get replies for parent comments
            replies = Comment.objects.filter(parent=obj)
            return CommentSerializer(replies, many=True).data
        return []

    def get_likes_count(self, obj):
        return obj.likes.count()

class RegistrationSerializer(serializers.ModelSerializer):
    attendee = UserSerializer(read_only=True)
    
    class Meta:
        model = Registration
        fields = ['id', 'event', 'attendee', 'status', 'registration_date', 
                 'cancelled_date', 'notes']
        read_only_fields = ['registration_date', 'cancelled_date']

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