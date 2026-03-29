FIXED_ADMIN_USERNAME = 'admin'


def is_fixed_admin(user):
    if user is None:
        return False
    return (getattr(user, 'username', '') or '').strip() == FIXED_ADMIN_USERNAME
