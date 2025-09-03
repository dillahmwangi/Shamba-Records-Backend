from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
        # Authentication endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    # Dashboard endpoints
    path('dashboard/admin/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('dashboard/farmer/', views.FarmerDashboardView.as_view(), name='farmer-dashboard'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/farmer/', views.FarmerProfileView.as_view(), name='farmer-profile'),
    
    # Farmer management endpoints (Admin only)
    path('farmers/', views.FarmerListCreateView.as_view(), name='farmer-list-create'),
    path('farmers/<int:pk>/', views.FarmerDetailView.as_view(), name='farmer-detail'),
    
    # Crop management endpoints
    path('crops/', views.CropListCreateView.as_view(), name='crop-list-create'),
    path('crops/<int:pk>/', views.CropDetailView.as_view(), name='crop-detail'),
    
    # Statistics endpoints
    path('statistics/crops/', views.crop_statistics, name='crop-statistics'),
]