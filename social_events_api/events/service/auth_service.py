from django.contrib.auth import authenticate
from ..utils.result import Result
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:
    def validate_login(self, data) -> Result:
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)
        
        if not user:
            return Result.failure('Unable to log in with provided credentials.')
                
        if not user.is_active:
            return Result.failure('User account is disabled.')
        
        return Result.success(user)
    
    def get_tokens_for_user(self, user):
        """Generate JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    def blacklist_token(self, refresh_token):
            token = RefreshToken(refresh_token)
            token.blacklist()

        
