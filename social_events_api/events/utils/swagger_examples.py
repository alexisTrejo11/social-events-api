_TOKEN_EXAMPLE = {
    'tokens': {
        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
    }
}

_AUTH_ERROR_EXAMPLES = {
    'VALIDATION_ERROR': {'detail': 'Invalid entry data'},
    'CONFLICT_ERROR': {'detail': 'Email/Phone-Number already taken'},
    'AUTH_ERROR': {'detail': 'Invalid credentials'},
    'TOKEN_ERROR': {'detail': 'Invalid token'}
}

_CATEGORY_EXAMPLE = {
        'id': 1,
        'name': 'Example Category',
        'description': 'This is an example category.',
        'created_at': '2023-10-01T12:00:00Z'
    }

CATEGORY_ERROR_EXAMPLES = {
        'VALIDATION_ERROR': {'detail': 'Invalid entry data'},
        'CONFLICT_ERROR': {'detail': 'Category with this name already exists'},
        'NOT_FOUND_ERROR': {'detail': 'Category not found'},
        'FORBIDDEN_ERROR': {'detail': 'You do not have permission to perform this action'}
    }

_COMMENT_EXAMPLE = {
    'id': 1,
    'text': 'Example comment text',
    'author': 'username',
    'created_at': '2025-01-24T14:22:00Z'
}

_COMMENT_LIST_EXAMPLE = [_COMMENT_EXAMPLE]

COMMENT_ERROR_EXAMPLES = {
    'VALIDATION_ERROR': {'detail': 'Invalid input data'},
    'FORBIDDEN_ERROR': {'detail': 'Not authorized for this action'},
    'NOT_FOUND_ERROR': {'detail': 'Resource not found'},
    'LIKE_ERROR': {'detail': 'Error processing like'}
}


_EVENT_EXAMPLE = {
    'id': 1,
    'title': 'Tech Conference',
    'description': 'Annual technology conference',
    'date': '2025-03-15T09:00:00Z',
    'location': 'Convention Center'
}
EVENT_ERROR_EXAMPLES = {
    'VALIDATION_ERROR': {'detail': 'Invalid event data'},
    'NOT_FOUND_ERROR': {'detail': 'Event not found'},
    'PERMISSION_ERROR': {'detail': 'You do not have permission for this action'},
    'FAVORITE_ERROR': {'detail': 'Error processing favorite status'}
}

_SUCCESS_MESSAGE = {'detail': 'Operation completed successfully'}


_REGISTRATION_EXAMPLE = {
    'id': 1,
    'event': 1,
    'attendee': 'username',
    'status': 'pending',
    'registration_date': '2025-01-24T14:22:00Z'
}
REGISTRATION_ERROR_EXAMPLES = {
    'VALIDATION_ERROR': {'detail': 'Invalid registration data'},
    'NOT_FOUND_ERROR': {'detail': 'Registration not found'},
    'PERMISSION_ERROR': {'detail': 'You do not have permission for this action'},
    'CONFLICT_ERROR': {'detail': 'Registration conflict'}
}


_USER_EXAMPLE = {
    'id': 1,
    'username': 'johndoe',
    'email': 'john@example.com',
    'date_joined': '2025-01-24T14:22:00Z'
}
USER_ERROR_EXAMPLES = {
    'VALIDATION_ERROR': {'detail': 'Invalid input data'},
    'SELF_FOLLOW_ERROR': {'detail': 'Cannot follow yourself'},
    'NOT_FOUND_ERROR': {'detail': 'User not found'}
}
