from celery import shared_task
import requests
from datetime import datetime

@shared_task
def generate_crm_report():
    url = "http://localhost:8000/graphql"
    
    query = """
    query {
        customersCount
        ordersCount
        totalRevenue
    }
    """

    try:
        response = requests.post(url, json={'query': query})
        data = response.json()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = "/tmp/crm_report_log.txt"

        with open(log_file, "a") as f:
            if "errors" in data:
                f.write(f"{now} ERROR: {data['errors']}\n")
            else:
                result = data["data"]
                f.write(
                    f"{now} - Report: {result['customersCount']} customers, "
                    f"{result['ordersCount']} orders, {result['totalRevenue']} revenue\n"
                )
    except Exception as e:
        with open("/tmp/crm_report_log.txt", "a") as f:
            f.write(f"EXCEPTION {str(e)}\n")
