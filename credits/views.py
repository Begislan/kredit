from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from .models import Credit, Payment, CreditHistory
from .forms import CreditForm, PaymentForm
from accounts.models import User

def home(request):
    return render(request, 'credits/home.html')

@login_required
def dashboard(request):
    user = request.user
    
    if user.user_type == 'lender':
        # Статистика кредитора
        credits = Credit.objects.filter(lender=user)
        active_credits = credits.filter(status='active')
        total_given = credits.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_remaining = credits.aggregate(total=Sum('remaining_amount'))['total'] or Decimal('0')
        total_interest = sum([c.get_total_with_interest() - c.amount for c in credits])
        
        context = {
            'credits': credits,
            'active_credits_count': active_credits.count(),
            'total_given': total_given,
            'total_remaining': total_remaining,
            'total_interest': total_interest,
        }
    else:
        # Статистика заемщика
        credits = Credit.objects.filter(borrower=user)
        active_credits = credits.filter(status='active')
        total_taken = credits.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_remaining = credits.aggregate(total=Sum('remaining_amount'))['total'] or Decimal('0')
        
        context = {
            'credits': credits,
            'active_credits_count': active_credits.count(),
            'total_taken': total_taken,
            'total_remaining': total_remaining,
        }
    
    return render(request, 'credits/dashboard.html', context)

@login_required
def credit_list(request):
    user = request.user
    
    if user.user_type == 'lender':
        credits = Credit.objects.filter(lender=user)
    else:
        credits = Credit.objects.filter(borrower=user)
    
    return render(request, 'credits/credit_list.html', {'credits': credits})

@login_required
def credit_create(request):
    if request.user.user_type != 'lender':
        messages.error(request, 'Для выдачи кредита вы должны быть кредитором!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CreditForm(request.POST)
        if form.is_valid():
            credit = form.save(commit=False)
            credit.lender = request.user
            credit.save()
            
            # Запись в историю
            CreditHistory.objects.create(
                credit=credit,
                action='Кредит создан',
                new_value=f"Сумма: {credit.amount}, Процент: {credit.interest_rate}%, Срок: {credit.duration_months} месяцев",
                changed_by=request.user
            )
            
            messages.success(request, 'Кредит успешно выдан!')
            return redirect('credit_detail', pk=credit.pk)
    else:
        form = CreditForm()
    
    return render(request, 'credits/credit_form.html', {'form': form, 'title': 'Новый кредит'})

@login_required
def credit_detail(request, pk):
    credit = get_object_or_404(Credit, pk=pk)
    
    # Проверка прав
    if request.user != credit.lender and request.user != credit.borrower:
        messages.error(request, 'У вас нет прав для просмотра этого кредита!')
        return redirect('dashboard')
    
    payments = credit.payments.all()
    
    context = {
        'credit': credit,
        'payments': payments,
        'total_paid': credit.get_paid_amount(),
        'remaining_percent': (credit.remaining_amount / credit.get_total_with_interest()) * 100 if credit.get_total_with_interest() > 0 else 0,
    }
    
    return render(request, 'credits/credit_detail.html', context)

@login_required
def make_payment(request, pk):
    credit = get_object_or_404(Credit, pk=pk)
    
    # Платеж может совершить только заемщик
    if request.user != credit.borrower:
        messages.error(request, 'Платеж может совершить только заемщик!')
        return redirect('credit_detail', pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.credit = credit
            
            # Проверка, чтобы сумма платежа не превышала остаток
            if payment.amount > credit.remaining_amount:
                messages.error(request, f'Сумма платежа не должна превышать остаток ({credit.remaining_amount} сом)!')
                return redirect('make_payment', pk=pk)
            
            payment.save()
            
            # Запись в историю
            CreditHistory.objects.create(
                credit=credit,
                action='Совершен платеж',
                new_value=f"Оплачено {payment.amount} сом",
                changed_by=request.user
            )
            
            messages.success(request, f'{payment.amount} сом оплачено!')
            return redirect('credit_detail', pk=pk)
    else:
        form = PaymentForm()
    
    return render(request, 'credits/payment_form.html', {'form': form, 'credit': credit})

@login_required
def credit_edit(request, pk):
    credit = get_object_or_404(Credit, pk=pk)
    
    if request.user != credit.lender:
        messages.error(request, 'Для редактирования кредита вы должны быть кредитором!')
        return redirect('credit_detail', pk=pk)
    
    if request.method == 'POST':
        form = CreditForm(request.POST, instance=credit)
        if form.is_valid():
            old_credit = Credit.objects.get(pk=pk)
            form.save()
            
            # Запись в историю
            CreditHistory.objects.create(
                credit=credit,
                action='Кредит изменен',
                old_value=f"Сумма: {old_credit.amount}, Процент: {old_credit.interest_rate}%",
                new_value=f"Сумма: {credit.amount}, Процент: {credit.interest_rate}%",
                changed_by=request.user
            )
            
            messages.success(request, 'Информация о кредите обновлена!')
            return redirect('credit_detail', pk=pk)
    else:
        form = CreditForm(instance=credit)
    
    return render(request, 'credits/credit_form.html', {'form': form, 'title': 'Редактировать кредит'})

@login_required
def reports(request):
    user = request.user
    
    if user.user_type == 'lender':
        credits = Credit.objects.filter(lender=user)
        
        # Статистика по месяцам
        monthly_stats = []
        for credit in credits:
            monthly_stats.append({
                'borrower': credit.borrower.username,
                'amount': credit.amount,
                'monthly_payment': credit.monthly_payment,
                'remaining': credit.remaining_amount,
                'status': credit.status,
            })
        
        context = {
            'total_credits': credits.count(),
            'total_amount': credits.aggregate(total=Sum('amount'))['total'] or 0,
            'total_remaining': credits.aggregate(total=Sum('remaining_amount'))['total'] or 0,
            'monthly_stats': monthly_stats,
        }
    else:
        credits = Credit.objects.filter(borrower=user)
        context = {
            'total_credits': credits.count(),
            'total_amount': credits.aggregate(total=Sum('amount'))['total'] or 0,
            'total_remaining': credits.aggregate(total=Sum('remaining_amount'))['total'] or 0,
            'active_credits': credits.filter(status='active').count(),
        }
    
    return render(request, 'credits/reports.html', context)