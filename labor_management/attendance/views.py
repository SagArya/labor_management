# attendance/views.py

from django.shortcuts import render, redirect
from .models import Worker, Site, Attendance, AdvancePayment, Salary
from datetime import datetime, timedelta
from django.db.models import Sum
from django.core.paginator import Paginator

def worker_list(request):
    workers = Worker.objects.all()
    return render(request, 'attendance/worker_list.html', {'workers': workers})

def add_worker(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        role = request.POST.get('role')
        daily_rate = request.POST.get('daily_rate')
        contact_info = request.POST.get('contact_info')
        Worker.objects.create(name=name, role=role, daily_rate=daily_rate, contact_info=contact_info)
        return redirect('worker_list')
    return render(request, 'attendance/worker_form.html')

def add_site(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        Site.objects.create(name=name, location=location)
        return redirect('site_list')
    return render(request, 'attendance/site_form.html')

def site_list(request):
    sites = Site.objects.all()
    return render(request, 'attendance/site_list.html', {'sites': sites})

def record_attendance(request):
    workers = Worker.objects.all()
    sites = Site.objects.all()
    attendance_records = Attendance.objects.all()

    # Filtering by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        attendance_records = attendance_records.filter(date__range=[start_date, end_date])

    # Filtering by worker
    worker_id = request.GET.get('worker_id')
    if worker_id:
        attendance_records = attendance_records.filter(worker__id=worker_id)

    # Filtering by site
    site_id = request.GET.get('site_id')
    if site_id:
        attendance_records = attendance_records.filter(site__id=site_id)

    # Sorting
    sort_by = request.GET.get('sort_by', '-date')
    if sort_by:
        attendance_records = attendance_records.order_by(sort_by)
    
     # Pagination
    paginator = Paginator(attendance_records, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        worker_id = request.POST.get('worker')
        site_id = request.POST.get('site')
        date = request.POST.get('date')
        present = 'present' in request.POST
        worker = Worker.objects.get(id=worker_id)
        site = Site.objects.get(id=site_id)
        Attendance.objects.create(worker=worker, site=site, date=date, present=present)
        
    # workers = Worker.objects.all()
    # sites = Site.objects.all()
    # attendance_records = Attendance.objects.all()
    return render(request, 'attendance/attendance_form.html', {
        'workers': workers,
        'sites': sites,
        'attendance_records': attendance_records,
        'start_date': start_date,
        'end_date': end_date,
        'worker_id': worker_id,
        'site_id': site_id,
        'sort_by': sort_by,
    })

def record_advance_payment(request):
    # Initial queryset
    queryset = AdvancePayment.objects.select_related('worker').order_by('-date')

    if request.method == 'POST':
        worker_id = request.POST.get('worker')
        date = request.POST.get('date')
        amount = request.POST.get('amount')
        worker = Worker.objects.get(id=worker_id)
        AdvancePayment.objects.create(worker=worker, date=date, amount=amount)
        return redirect('record_advance_payment')
    
     # Filter by date
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        queryset = queryset.filter(date__range=[start_date, end_date])

    # Filter by worker
    worker_id = request.GET.get('worker_id')
    if worker_id:
        queryset = queryset.filter(worker_id=worker_id)
    
    workers = Worker.objects.all()
    

    context = {
        'workers': workers,
        'advance_payments': queryset,
    }
    return render(request, 'attendance/advance_payment_form.html', context)

def calculate_salary(request):
    workers = Worker.objects.all()

    if request.method == 'POST':
        try:
            worker_id = request.POST.get('worker_id')
            end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d')
            start_date = end_date - timedelta(days=6)

            worker = Worker.objects.get(id=worker_id)
            attendances = Attendance.objects.filter(worker=worker, date__range=[start_date, end_date], present=True)
            total_days_worked = attendances.count()

            total_salary = total_days_worked * worker.daily_rate

            advance_payments = AdvancePayment.objects.filter(worker=worker, date__range=[start_date, end_date])
            total_advance = advance_payments.aggregate(Sum('amount'))['amount__sum'] or 0
            net_salary = total_salary - total_advance

            # Create or update Salary object
            salary_obj, created = Salary.objects.update_or_create(
                worker=worker,
                week_ending=end_date,
                defaults={
                    'total_days_worked': total_days_worked,
                    'total_salary': total_salary,
                    'advances_deducted': total_advance,
                    'net_salary': net_salary
                }
            )

            return render(request, 'attendance/calculate_salary.html', {
                'workers': workers,
                'salary_obj': salary_obj,
                'created': created  # Pass a flag to indicate if a new record was created or updated
            })

        except Worker.DoesNotExist:
            return render(request, 'attendance/error.html', {'message': 'Worker not found'})
        except Exception as e:
            print(f"Error in calculate_salary view: {e}")
            return render(request, 'attendance/error.html', {'message': 'An error occurred'})

    return render(request, 'attendance/calculate_salary.html', {'workers': workers})