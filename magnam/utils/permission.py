from rest_framework.permissions import BasePermission
from ProfilePageApp.models import Profile
from PortfolioPageApp.models import Portfolio
from MangaPageApp.models import Manga, Chapter
from KanbanTaskPageApp.models import KanbanTask


def is_user_admin(user):
    return user.is_superuser


def has_permission(user, permission_type):
    if user.is_authenticated and is_user_admin(user):
        return True  # Admin can do everything

    if user.is_authenticated and permission_type != "admin":
        return True  # Logged in and not admin permission

    if not user.is_authenticated and permission_type == "guest":
        return True  # Guest users can only do guest stuff

    return False


class PermissionCheck(BasePermission):
    def has_permission(self, request, view):
        permission_type = getattr(view, "permission_type", "guest")
        return has_permission(request.user, permission_type)

    def has_object_permission(self, request, view, obj):
        permission_type = getattr(view, "permission_type", "guest")
        user = request.user

        if user.is_authenticated and is_user_admin(user):
            return True  # Admin can do everything

        # request sender must be the owner of the requested object
        request_sender_id = user.profile.id
        if isinstance(obj, Profile):  # profile owner
            id_check = obj.id
        elif isinstance(obj, Portfolio):  # portfolio owner
            id_check = obj.owner.id
        elif isinstance(obj, KanbanTask):  # task owner
            id_check = obj.creator.id
        elif isinstance(
            obj, Manga
        ):  # only manga owner is allowed to do manga-level stuff
            id_check = obj.owner.id
        elif isinstance(obj, list):
            """
            chapter.owner, chapter.manga.owner (and in chapter creation chapter.manga.collaborators) are allowed to do chapter-level stuff
            here simple "id_check == request_sender_id" check doesn't fully work
            so we need to know if the request sender is in this set of permission holder profiles

            obj is a list like this in editing:
            [manga.owner, chapter.owner]
            or
            something like this in the chapter creation request:
            [manga.owner] + [manga.collaborators]
            """

            request_sender = user.profile
            if request_sender in obj:
                # if request_sender has permission: set the id_check to pass the id check
                id_check = request_sender.id
            else:  # else set it to -1 so it doesn't pass the id check
                id_check = -1
        elif isinstance(
            obj, Chapter
        ):  # this condition is checked only when a chapter is being submitted to a competition
            # even the manga owner can't submit a chapter under his own manga if it isn't his
            id_check = obj.owner.id

        if (
            user.is_authenticated
            and permission_type != "admin"
            and id_check == request_sender_id
        ):
            return True  # Logged in, not admin, and owner matches user.profile.id

        return False
