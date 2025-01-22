from django.contrib.auth import authenticate
from ..utils.result import Result

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
