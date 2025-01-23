from ..models import Registration, User, Event
from ..utils.result import Result
from django.core.exceptions import ValidationError

class RegistrationService:

    def validate_authority(self, registration :  Registration, user: User):
       if registration.attendee != user:
            raise ValidationError("Not allowed to make this action") 

    def validate_creation(self, data : dict):
        event = data.get('event')
        attendee = data.get('attendee')
        
        is_registration_existing = Registration.objects.filter(attendee=attendee, event=event).exists()
        if is_registration_existing:
            return Result.failure("Registration already exists")
    
        if event.status == 'cancelled':
            return Result.failure("Can't make registration of a cancelled event")

        if Registration.objects.filter(event=event, attendee=attendee).exists():
            return Result.failure("Already registred at the event")

        if event.capacity and event.registrations.count() >= event.capacity:
            return Result.failure("The event has reached its maximum capacity.")
        
        return Result.success()
    
    def create(self, data) -> Registration:        
        return Registration.objects.create(**data)
    
    def confirm(self, registration : Registration):
        self.__validate_confirm(registration)

        registration.status = 'confirmed'
        registration.save()
    
    def cancel(self, registration : Registration):
        if registration.status == 'pending':
            self.__delete_registration(registration)
        elif registration.status == 'confirmed':
            self.__cancel_registration(registration)
        else:
            self.__undo_cancel(registration)

    def __cancel_registration(self, registration):
        registration.status = 'pending'
        registration.cancelled_date = None
        registration.save()

    def __undo_cancel(self, registration):
        registration.status = 'pending'
        registration.cancelled_date = None
        registration.save()

    def __delete_registration(self, registration):
        registration.delete()

    def __validate_confirm(self, registration):
        if registration.status != 'pending':
            raise ValidationError("Only pending registrations can be confirmed")
    

