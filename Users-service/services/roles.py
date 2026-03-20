from pydantic import BaseModel


class NotePermissions(BaseModel):
    """Права на работу с заметками"""

    create_own: bool = False
    read_own: bool = False
    edit_own: bool = False
    delete_own: bool = False
    read_all: bool = False
    edit_all: bool = False
    delete_all: bool = False


class ProfilePermissions(BaseModel):
    """Права на работу с профилем"""

    view_own: bool = False
    edit_own: bool = False
    change_password: bool = False
    change_avatar: bool = False
    delete_own: bool = False


class UserManagementPermissions(BaseModel):
    """Права на управление пользователями"""

    view_all_users: bool = False
    create_users: bool = False
    edit_users: bool = False
    delete_users: bool = False
    block_users: bool = False
    change_roles: bool = False


class SystemPermissions(BaseModel):
    """Системные права"""

    access_admin_panel: bool = False
    view_logs: bool = False
    manage_settings: bool = False
    monitor_system: bool = False
    manage_storage: bool = False
    view_analytics: bool = False


class AccessRights(BaseModel):
    """Полный набор прав доступа"""

    notes: NotePermissions
    profile: ProfilePermissions
    user_management: UserManagementPermissions
    system: SystemPermissions


class UserPermissions:
    """Базовый класс прав доступа"""

    name: str
    description: str
    rights: AccessRights


class RegularUser(UserPermissions):
    """Обычный пользователь"""

    name = "user"
    description = "Обычный пользователь"
    rights = AccessRights(
        notes=NotePermissions(
            create_own=True,
            read_own=True,
            edit_own=True,
            delete_own=True,
            read_all=False,
            edit_all=False,
            delete_all=False,
        ),
        profile=ProfilePermissions(
            view_own=True,
            edit_own=True,
            change_password=True,
            change_avatar=True,
            delete_own=True,
        ),
        user_management=UserManagementPermissions(
            view_all_users=False,
            create_users=False,
            edit_users=False,
            delete_users=False,
            block_users=False,
            change_roles=False,
        ),
        system=SystemPermissions(
            access_admin_panel=False,
            view_logs=False,
            manage_settings=False,
            monitor_system=False,
            manage_storage=False,
            view_analytics=False,
        ),
    )


class AdminUser(UserPermissions):
    """Администратор"""

    name = "admin"
    description = "Администратор системы"
    rights = AccessRights(
        notes=NotePermissions(
            create_own=True,
            read_own=True,
            edit_own=True,
            delete_own=True,
            read_all=True,
            edit_all=True,
            delete_all=True,
        ),
        profile=ProfilePermissions(
            view_own=True,
            edit_own=True,
            change_password=True,
            change_avatar=True,
            delete_own=True,
        ),
        user_management=UserManagementPermissions(
            view_all_users=True,
            create_users=True,
            edit_users=True,
            delete_users=True,
            block_users=True,
            change_roles=True,
        ),
        system=SystemPermissions(
            access_admin_panel=True,
            view_logs=True,
            manage_settings=True,
            monitor_system=True,
            manage_storage=True,
            view_analytics=True,
        ),
    )


class ModeratorUser(UserPermissions):
    """Модератор"""

    name = "moderator"
    description = "Модератор контента"
    rights = AccessRights(
        notes=NotePermissions(
            create_own=True,
            read_own=True,
            edit_own=True,
            delete_own=True,
            read_all=True,
            edit_all=True,
            delete_all=True,
        ),
        profile=ProfilePermissions(
            view_own=True,
            edit_own=True,
            change_password=True,
            change_avatar=True,
            delete_own=True,
        ),
        user_management=UserManagementPermissions(
            view_all_users=True,
            create_users=False,
            edit_users=False,
            delete_users=False,
            block_users=True,
            change_roles=False,
        ),
        system=SystemPermissions(
            access_admin_panel=False,
            view_logs=True,
            manage_settings=False,
            monitor_system=False,
            manage_storage=False,
            view_analytics=True,
        ),
    )


class ReadOnlyUser(UserPermissions):
    """Пользователь только для чтения"""

    name = "readonly"
    description = "Пользователь с правами только на чтение"
    rights = AccessRights(
        notes=NotePermissions(
            create_own=False,
            read_own=True,
            edit_own=False,
            delete_own=False,
            read_all=False,
            edit_all=False,
            delete_all=False,
        ),
        profile=ProfilePermissions(
            view_own=True,
            edit_own=False,
            change_password=True,
            change_avatar=False,
            delete_own=False,
        ),
        user_management=UserManagementPermissions(
            view_all_users=False,
            create_users=False,
            edit_users=False,
            delete_users=False,
            block_users=False,
            change_roles=False,
        ),
        system=SystemPermissions(
            access_admin_panel=False,
            view_logs=False,
            manage_settings=False,
            monitor_system=False,
            manage_storage=False,
            view_analytics=False,
        ),
    )


class GuestUser(UserPermissions):
    """Гостевой пользователь"""

    name = "guest"
    description = "Гостевой доступ"
    rights = AccessRights(
        notes=NotePermissions(
            create_own=False,
            read_own=False,
            edit_own=False,
            delete_own=False,
            read_all=False,
            edit_all=False,
            delete_all=False,
        ),
        profile=ProfilePermissions(
            view_own=True,
            edit_own=False,
            change_password=False,
            change_avatar=False,
            delete_own=False,
        ),
        user_management=UserManagementPermissions(
            view_all_users=False,
            create_users=False,
            edit_users=False,
            delete_users=False,
            block_users=False,
            change_roles=False,
        ),
        system=SystemPermissions(
            access_admin_panel=False,
            view_logs=False,
            manage_settings=False,
            monitor_system=False,
            manage_storage=False,
            view_analytics=False,
        ),
    )

ALL_ROLES = {
    "user": RegularUser(),
    "admin": AdminUser(),
    "moderator": ModeratorUser(),
    "readonly": ReadOnlyUser(),
    "guest": GuestUser(),
}
