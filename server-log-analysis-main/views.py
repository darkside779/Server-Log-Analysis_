from django.shortcuts import render
from .models import LogEntry
from django.utils.dateparse import parse_datetime

def log_dashboard(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    ip_filter = request.GET.get('ip')
    
    logs = LogEntry.objects.all()
    
    if start_date and end_date:
        logs = logs.filter(datetime__range=[parse_datetime(start_date), parse_datetime(end_date)])
    
    if ip_filter:
        logs = logs.filter(ip=ip_filter)

    context = {'logs': logs}
    return render(request, 'dashboard.html', context)
