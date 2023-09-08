from functools import wraps
from django.shortcuts import redirect

def active_non_superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_active and not request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            return redirect('user_signin') 
    return _wrapped_view


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            return redirect('admin_signin') 
    return _wrapped_view