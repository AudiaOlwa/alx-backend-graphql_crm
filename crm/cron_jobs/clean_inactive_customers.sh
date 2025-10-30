#!/bin/bash

LOG_FILE="/tmp/customer_cleanup_log.txt"

deleted=$(python3 << 'EOF'
import sys, os, django
from django.utils import timezone
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../.."))
sys.path.append(PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql.settings")
django.setup()

from crm.models import Customer
from django.db.models import Max

one_year_ago = timezone.now() - timedelta(days=365)

customers = Customer.objects.annotate(
    last_order_date=Max('orders__order_date')
).filter(
    last_order_date__lt=one_year_ago
) | Customer.objects.filter(orders__isnull=True)

count = customers.count()
customers.delete()
print(count)
EOF
)

echo "$(date): Deleted $deleted inactive customers" >> $LOG_FILE
