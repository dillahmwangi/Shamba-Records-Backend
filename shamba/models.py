# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class User(AbstractUser):
    """Extended user model with role-based access"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('farmer', 'Farmer'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='farmer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_farmer(self):
        return self.role == 'farmer'

class Farmer(models.Model):
    """Farmer profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    farm_name = models.CharField(max_length=200, blank=True, null=True)
    farm_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
    validators=[MinValueValidator(Decimal('0.01'))])
    location = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.farm_name}"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

class Crop(models.Model):
    """Crop model linked to farmers"""
    CROP_TYPES = [
        ('cereals', 'Cereals'),
        ('legumes', 'Legumes'),
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('cash_crops', 'Cash Crops'),
        ('other', 'Other'),
    ]
    
    CROP_STATUS = [
        ('planted', 'Planted'),
        ('growing', 'Growing'),
        ('harvested', 'Harvested'),
        ('sold', 'Sold'),
    ]
    
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='crops')
    name = models.CharField(max_length=100)
    crop_type = models.CharField(max_length=20, choices=CROP_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, 
                                  validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=20, default='kg')
    planting_date = models.DateField(blank=True, null=True)
    expected_harvest_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=CROP_STATUS, default='planted')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.farmer.full_name} ({self.quantity} {self.unit})"