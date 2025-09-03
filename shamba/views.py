# views.py
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import login, logout
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from collections import defaultdict

from .models import User, Farmer, Crop
from .serializers import (
    UserRegistrationSerializer, LoginSerializer, UserSerializer,
    FarmerSerializer, FarmerCreateSerializer, CropSerializer, 
    CropCreateUpdateSerializer, DashboardSerializer, FarmerDashboardSerializer
)
from .permissions import IsAdminUser, IsFarmerUser, IsOwnerOrAdmin, IsCropOwnerOrAdmin

# Authentication Views
class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'User created successfully',
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            
            # Get additional user data based on role
            user_data = UserSerializer(user).data
            if user.is_farmer and hasattr(user, 'farmer_profile'):
                user_data['farmer_profile'] = FarmerSerializer(user.farmer_profile).data
            
            return Response({
                'message': 'Login successful',
                'user': user_data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Delete the user's token
            request.user.auth_token.delete()
        except:
            pass
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

# Dashboard Views
class AdminDashboardView(APIView):
    """Admin dashboard with statistics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Get statistics
        total_farmers = Farmer.objects.count()
        total_crops = Crop.objects.count()
        
        # Crops by type
        crops_by_type = dict(Crop.objects.values('crop_type').annotate(
            count=Count('crop_type')
        ).values_list('crop_type', 'count'))
        
        # Recent crops (last 10)
        recent_crops = Crop.objects.select_related('farmer__user').order_by('-created_at')[:10]
        
        data = {
            'total_farmers': total_farmers,
            'total_crops': total_crops,
            'crops_by_type': crops_by_type,
            'recent_crops': CropSerializer(recent_crops, many=True).data
        }
        
        return Response(data)

class FarmerDashboardView(APIView):
    """Farmer dashboard with their statistics"""
    permission_classes = [IsFarmerUser]
    
    def get(self, request):
        farmer = get_object_or_404(Farmer, user=request.user)
        
        # Get farmer's crop statistics
        farmer_crops = Crop.objects.filter(farmer=farmer)
        total_crops = farmer_crops.count()
        
        # Crops by type
        crops_by_type = dict(farmer_crops.values('crop_type').annotate(
            count=Count('crop_type')
        ).values_list('crop_type', 'count'))
        
        # Crops by status
        crops_by_status = dict(farmer_crops.values('status').annotate(
            count=Count('status')
        ).values_list('status', 'count'))
        
        # Recent crops
        recent_crops = farmer_crops.order_by('-created_at')[:5]
        
        data = {
            'total_crops': total_crops,
            'crops_by_type': crops_by_type,
            'crops_by_status': crops_by_status,
            'recent_crops': CropSerializer(recent_crops, many=True).data
        }
        
        return Response(data)

# Farmer Management Views (Admin only)
class FarmerListCreateView(generics.ListCreateAPIView):
    """List all farmers or create a new farmer (Admin only)"""
    permission_classes = [IsAdminUser]
    queryset = Farmer.objects.select_related('user').all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FarmerCreateSerializer
        return FarmerSerializer

class FarmerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a farmer (Admin only)"""
    permission_classes = [IsAdminUser]
    queryset = Farmer.objects.select_related('user').all()
    serializer_class = FarmerSerializer
    
    def destroy(self, request, *args, **kwargs):
        farmer = self.get_object()
        user = farmer.user
        farmer.delete()
        user.delete()  # Also delete the associated user
        return Response({'message': 'Farmer deleted successfully'}, 
                       status=status.HTTP_204_NO_CONTENT)

# Farmer Profile Views
class FarmerProfileView(APIView):
    """Farmer's own profile view and update"""
    permission_classes = [IsFarmerUser]
    
    def get(self, request):
        farmer = get_object_or_404(Farmer, user=request.user)
        serializer = FarmerSerializer(farmer)
        return Response(serializer.data)
    
    def put(self, request):
        farmer = get_object_or_404(Farmer, user=request.user)
        
        # Update user fields
        user_fields = ['first_name', 'last_name', 'email', 'phone', 'address']
        for field in user_fields:
            if field in request.data:
                setattr(request.user, field, request.data[field])
        request.user.save()
        
        # Update farmer fields
        farmer_serializer = FarmerSerializer(farmer, data=request.data, partial=True)
        if farmer_serializer.is_valid():
            farmer_serializer.save()
            return Response(farmer_serializer.data)
        return Response(farmer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Crop Management Views
class CropListCreateView(APIView):
    """List and create crops with role-based filtering"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.is_admin:
            # Admin sees all crops
            crops = Crop.objects.select_related('farmer__user').all()
        else:
            # Farmer sees only their crops
            farmer = get_object_or_404(Farmer, user=request.user)
            crops = Crop.objects.filter(farmer=farmer)
        
        # Add filtering by crop_type and status
        crop_type = request.query_params.get('crop_type')
        status_filter = request.query_params.get('status')
        
        if crop_type:
            crops = crops.filter(crop_type=crop_type)
        if status_filter:
            crops = crops.filter(status=status_filter)
        
        serializer = CropSerializer(crops, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if request.user.is_farmer:
            farmer = get_object_or_404(Farmer, user=request.user)
        else:
            # Admin can create crops for any farmer
            farmer_id = request.data.get('farmer_id')
            if not farmer_id:
                return Response({'error': 'farmer_id is required for admin'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            farmer = get_object_or_404(Farmer, id=farmer_id)
        
        serializer = CropCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            crop = serializer.save(farmer=farmer)
            return Response(CropSerializer(crop).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CropDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific crop"""
    permission_classes = [IsCropOwnerOrAdmin]
    queryset = Crop.objects.select_related('farmer__user').all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CropCreateUpdateSerializer
        return CropSerializer

# User Management Views
class UserProfileView(APIView):
    """Current user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Statistics Views
@api_view(['GET'])
@permission_classes([IsAdminUser])
def crop_statistics(request):
    """Get detailed crop statistics for admin"""
    crops_by_farmer = Crop.objects.values('farmer__user__first_name', 'farmer__user__last_name') \
        .annotate(count=Count('id')).order_by('-count')[:10]
    
    crops_by_month = Crop.objects.extra(
        select={'month': "date_format(created_at, '%%Y-%%m')"}
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    return Response({
        'crops_by_farmer': list(crops_by_farmer),
        'crops_by_month': list(crops_by_month),
    })
