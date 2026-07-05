WAREHOUSE_PERMISSION_FIELDS = [
    ('perm_dashboard', 'Αρχική Αποθήκη'),
    ('perm_view_products', 'Προβολή Υλικών'),
    ('perm_create_products', 'Δημιουργία Υλικών'),
    ('perm_edit_products', 'Επεξεργασία Υλικών'),
    ('perm_delete_products', 'Διαγραφή Υλικών'),
    ('perm_add_quantity', 'Προσθήκη Ποσότητας'),
    ('perm_remove_quantity', 'Αφαίρεση Ποσότητας'),
    ('perm_measurement_units', 'Μονάδες Μέτρησης'),
    ('perm_products', 'Προϊόντα'),
    ('perm_finished_products_warehouse', 'Αποθήκη Έτοιμων Προϊόντων'),
    ('perm_offers', 'Προσφορές'),
    ('perm_customers', 'Πελάτες'),
]

WAREHOUSE_PERMISSION_KEYS = [key for key, _ in WAREHOUSE_PERMISSION_FIELDS]

MODULE_PERMISSION_KEYS = frozenset({
    'perm_products',
    'perm_finished_products_warehouse',
    'perm_offers',
    'perm_customers',
})


def get_warehouse_profile(user):
    if not user.is_authenticated:
        return None
    from .models import WarehouseUserProfile
    try:
        return user.warehouse_profile
    except WarehouseUserProfile.DoesNotExist:
        return None


def is_warehouse_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = get_warehouse_profile(user)
    return profile is not None and profile.role == profile.ROLE_ADMIN


def has_warehouse_perm(user, perm_key):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = get_warehouse_profile(user)
    if profile is None:
        return False
    if profile.role == profile.ROLE_ADMIN:
        return True
    return bool(getattr(profile, perm_key, False))


def has_module_perm(user, perm_key):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = get_warehouse_profile(user)
    if profile is None:
        return True
    if profile.role == profile.ROLE_ADMIN:
        return True
    if not profile.is_managed_user:
        return True
    return bool(getattr(profile, perm_key, False))


def has_any_warehouse_access(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = get_warehouse_profile(user)
    if profile is None:
        return False
    if profile.role == profile.ROLE_ADMIN:
        return True
    return any(getattr(profile, key, False) for key in WAREHOUSE_PERMISSION_KEYS)


def get_permissions_dict(user):
    return {
        key: (
            has_module_perm(user, key)
            if key in MODULE_PERMISSION_KEYS
            else has_warehouse_perm(user, key)
        )
        for key in WAREHOUSE_PERMISSION_KEYS
    }


def can_access_warehouse_dashboard(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or is_warehouse_admin(user):
        return True
    profile = get_warehouse_profile(user)
    if profile is None:
        return False
    return any(
        getattr(profile, perm_key, False)
        for perm_key in (
            'perm_dashboard',
            'perm_view_products',
            'perm_add_quantity',
            'perm_remove_quantity',
        )
    )


WAREHOUSE_HOME_PRIORITY = [
    ('perm_dashboard', 'warehouse:dashboard'),
    ('perm_view_products', 'warehouse:product_list'),
    ('perm_add_quantity', 'warehouse:quantity_select_add'),
    ('perm_remove_quantity', 'warehouse:quantity_select_remove'),
    ('perm_create_products', 'warehouse:product_create'),
    ('perm_measurement_units', 'warehouse:settings'),
]


def get_warehouse_home_url_name(user):
    if not user.is_authenticated:
        return 'dashboard'
    if user.is_superuser:
        return 'warehouse:dashboard'
    profile = get_warehouse_profile(user)
    if profile is None:
        return 'dashboard'
    if profile.role == profile.ROLE_ADMIN:
        return 'warehouse:dashboard'
    if can_access_warehouse_dashboard(user):
        return 'warehouse:dashboard'
    for perm_key, url_name in WAREHOUSE_HOME_PRIORITY:
        if perm_key in (
            'perm_dashboard',
            'perm_view_products',
            'perm_add_quantity',
            'perm_remove_quantity',
        ):
            continue
        if getattr(profile, perm_key, False):
            return url_name
    return 'dashboard'
