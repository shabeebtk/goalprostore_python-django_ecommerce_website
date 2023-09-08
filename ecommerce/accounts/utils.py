from .models import CustomUser

def get_user_email_from_db(request):
    """Retrieves the user's email address from the database."""
    user_id = request.user.id
    user = CustomUser.objects.get(id=user_id)
    return user.email