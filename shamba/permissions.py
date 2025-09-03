# permissions.py
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to allow only admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin

class IsFarmerUser(permissions.BasePermission):
    """
    Custom permission to allow only farmer users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_farmer

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners of an object or admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_admin:
            return True
        
        # For Farmer model
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For Crop model
        if hasattr(obj, 'farmer'):
            return obj.farmer.user == request.user
        
        return False

class IsCropOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission specifically for crops - allows crop owner or admin.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin can access all crops
        if request.user.is_admin:
            return True
        
        # Farmer can only access their own crops
        return obj.farmer.user == request.user