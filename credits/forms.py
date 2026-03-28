from django import forms
from .models import Credit, Payment
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class CreditForm(forms.ModelForm):
    class Meta:
        model = Credit
        fields = ['borrower', 'amount', 'interest_rate', 'duration_months']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'borrower': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Бул жерде borrower талаасынын querysetин аныктайбыз
        self.fields['borrower'].queryset = User.objects.filter(user_type='borrower')

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }