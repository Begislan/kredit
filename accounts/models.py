from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from decimal import Decimal

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('lender', 'Кредит берүүчү'),
        ('borrower', 'Кредит алуучу'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"
    
    def get_total_credits_given(self):
        if self.user_type == 'lender':
            total = self.credits_given.aggregate(total=Sum('amount'))['total']
            return total or Decimal('0')
        return Decimal('0')
    
    def get_total_credits_taken(self):
        if self.user_type == 'borrower':
            total = self.credits_taken.aggregate(total=Sum('amount'))['total']
            return total or Decimal('0')
        return Decimal('0')
    
    @property
    def credits_given_filter_active(self):
        return self.credits_given.filter(status='active')