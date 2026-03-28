from fastapi import FastAPI
from sqladmin import Admin, ModelView

from core.models.users import User


class UserAdminView(ModelView, model=User):
    can_create = True
    column_list = ("id", "username", "avatar_links")
    form_columns = ("id", "username", "avatar_links")


def setup_admin(app: FastAPI, engine):
    admin = Admin(app, engine, title="Admin panel")
    admin.add_view(UserAdminView)
