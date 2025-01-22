from ..models import User
from django.contrib.auth.hashers import make_password
from ..utils.result import Result
from typing import Dict, Any, Optional
import re

class UserService:
    def validate(self, data: Dict[Any, Any]) -> Result:  
        """
        Username automatic unique evaluation by Django
        """

        if self.__is_email_taken(data.get('email')):
            Result.failure("Email Already Taken")

        password_result = self.__validate_password(data.get('password'))
        if not password_result.success:
            return password_result 
        
        return Result.success()

    def create(self, data: Dict[Any, Any]):        
        self.__hash_pasword(data)
        user = User.objects.create_user(**data)
        return user

    
    def __hash_pasword(self, data: Dict[Any, Any]):
        password = data.pop('password')
        data['password'] = make_password(password)

    def __validate_password(self, password: str) -> Result:
        if not (8 <= len(password) <= 100):
            return Result.failure("The password length must be between 8 and 100 characters")
    
        if not re.search(r"[a-z]", password):
            return Result.failure("The password must contain at least one lowercase letter")

        if not re.search(r"[A-Z]", password):
            return Result.failure("The password must contain at least one uppercase letter")

        if not re.search(r"\d", password):
            return Result.failure("The password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return Result.failure("The password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
           
        return Result.success()
    
    def __is_email_taken(self, request_email) -> bool:
        return User.objects.filter(email=request_email).exists

    def __is_username_taken(self, username) -> bool:
        return User.objects.filter(username=username).exists



