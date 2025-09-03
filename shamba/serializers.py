# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Farmer, Crop

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 
                 'first_name', 'last_name', 'phone', 'address']
        
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        
        # Create farmer profile for farmer users
        if user.role == 'farmer':
            Farmer.objects.create(user=user)
        
        return user

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must provide username and password')
        
        return attrs

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'phone', 'address', 'role', 'date_joined']
        read_only_fields = ['id', 'username', 'role', 'date_joined']

class FarmerSerializer(serializers.ModelSerializer):
    """Serializer for farmer profile"""
    user = UserSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    crops_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Farmer
        fields = ['id', 'user', 'full_name', 'farm_name', 'farm_size', 
                 'location', 'crops_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_crops_count(self, obj):
        return obj.crops.count()

class FarmerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating farmers"""
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Farmer
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                 'phone', 'address', 'farm_name', 'farm_size', 'location']
    
    def create(self, validated_data):
        # Extract user data
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'phone': validated_data.pop('phone', ''),
            'address': validated_data.pop('address', ''),
            'role': 'farmer'
        }
        
        # Create user
        user = User.objects.create_user(**user_data)
        
        # Create farmer profile
        farmer = Farmer.objects.create(user=user, **validated_data)
        return farmer

class CropSerializer(serializers.ModelSerializer):
    """Serializer for crop data"""
    farmer_name = serializers.SerializerMethodField()
    crop_type_display = serializers.CharField(source='get_crop_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Crop
        fields = ['id', 'name', 'crop_type', 'crop_type_display', 'quantity', 'unit',
                 'planting_date', 'expected_harvest_date', 'status', 'status_display',
                 'notes', 'farmer', 'farmer_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'farmer_name']
    
    def get_farmer_name(self, obj):
        return obj.farmer.full_name

class CropCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating crops"""
    class Meta:
        model = Crop
        fields = ['name', 'crop_type', 'quantity', 'unit', 'planting_date', 
                 'expected_harvest_date', 'status', 'notes']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    total_farmers = serializers.IntegerField()
    total_crops = serializers.IntegerField()
    crops_by_type = serializers.DictField()
    recent_crops = CropSerializer(many=True)

class FarmerDashboardSerializer(serializers.Serializer):
    """Serializer for farmer dashboard data"""
    total_crops = serializers.IntegerField()
    crops_by_type = serializers.DictField()
    crops_by_status = serializers.DictField()
    recent_crops = CropSerializer(many=True)