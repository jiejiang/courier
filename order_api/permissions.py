from rest_framework import permissions

class IsApiUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.api_profile.can_use_api

class IsRequestOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsPackageOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.request.owner == request.user
