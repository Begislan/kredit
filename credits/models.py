from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

class Credit(models.Model):
    STATUS_CHOICES = (
        ('active', 'Активдүү'),
        ('closed', 'Жабылган'),
        ('overdue', 'Мөөнөтү өткөн'),
    )
    
    lender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               related_name='credits_given', limit_choices_to={'user_type': 'lender'})
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                 related_name='credits_taken', limit_choices_to={'user_type': 'borrower'})
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Кредит суммасы')
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Проценттик ставка (%)')
    duration_months = models.IntegerField(verbose_name='Мөөнөт (ай)')
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Калган сумма')
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Айлык төлөм')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.pk:
            # Кредиттин жалпы суммасын эсептөө (процент менен)
            total_with_interest = self.amount * (1 + self.interest_rate / 100)
            self.remaining_amount = total_with_interest
            self.monthly_payment = total_with_interest / self.duration_months
            # Кредиттин аяктаган күнүн эсептөө
            self.end_date = timezone.now() + timedelta(days=self.duration_months * 30)
        super().save(*args, **kwargs)
    
    def get_total_with_interest(self):
        return self.amount * (1 + self.interest_rate / 100)
    
    def get_paid_amount(self):
        return self.get_total_with_interest() - self.remaining_amount
    
    def __str__(self):
        return f"{self.borrower.username} - {self.amount} сом"
    
    def update_remaining(self):
        """Калган сумманы жаңыртуу"""
        payments = self.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        self.remaining_amount = self.get_total_with_interest() - payments
        if self.remaining_amount <= 0:
            self.status = 'closed'
        self.save()

class Payment(models.Model):
    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Төлөм суммасы')
    payment_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, verbose_name='Түшүндүрмө')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.credit.update_remaining()
    
    def __str__(self):
        return f"{self.credit.borrower.username} - {self.amount} сом - {self.payment_date}"

class CreditHistory(models.Model):
    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50, verbose_name='Аракет')
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.credit} - {self.action} - {self.created_at}"