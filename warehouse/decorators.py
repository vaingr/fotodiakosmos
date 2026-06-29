from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect

from .permissions import (
    has_warehouse_perm,
    is_warehouse_admin,
    has_any_warehouse_access,
    get_warehouse_home_url_name,
    can_access_warehouse_dashboard,
)


def require_warehouse_access(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not has_any_warehouse_access(request.user):
            messages.error(request, 'Δεν έχετε πρόσβαση στην αποθήκη.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def require_warehouse_perm(perm_key):
    def decorator(view_func):
        @require_warehouse_access
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not has_warehouse_perm(request.user, perm_key):
                messages.error(request, 'Δεν έχετε δικαίωμα για αυτή την ενέργεια.')
                return redirect(get_warehouse_home_url_name(request.user))
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def require_warehouse_dashboard_access(view_func):
    @require_warehouse_access
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not can_access_warehouse_dashboard(request.user):
            messages.error(request, 'Δεν έχετε δικαίωμα για αυτή την ενέργεια.')
            return redirect(get_warehouse_home_url_name(request.user))
        return view_func(request, *args, **kwargs)
    return _wrapped


def require_warehouse_admin(view_func):
    @require_warehouse_access
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_warehouse_admin(request.user):
            messages.error(request, 'Μόνο οι διαχειριστές αποθήκης μπορούν να εκτελέσουν αυτή την ενέργεια.')
            return redirect('warehouse:settings')
        return view_func(request, *args, **kwargs)
    return _wrapped
