from .permissions import (
    get_permissions_dict,
    is_warehouse_admin,
    has_any_warehouse_access,
    get_warehouse_home_url_name,
)


def warehouse_permissions(request):
    if not request.user.is_authenticated:
        return {
            'wh_perms': {},
            'wh_is_admin': False,
            'wh_has_access': False,
            'wh_home_url': 'dashboard',
        }
    return {
        'wh_perms': get_permissions_dict(request.user),
        'wh_is_admin': is_warehouse_admin(request.user),
        'wh_has_access': has_any_warehouse_access(request.user),
        'wh_home_url': get_warehouse_home_url_name(request.user),
    }
