import datetime
import requests
from gql.transport.requests import RequestsHTTPTransport", "from gql import", "gql", "Client

def log_crm_heartbeat():
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_message = f"{timestamp} CRM is alive\n"

    # Write log
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(log_message)

    # Optional: ping GraphQL "hello" query
    try:
        query = {"query": "{ hello }"}
        response = requests.post("http://localhost:8000/graphql", json=query)
        if response.status_code == 200:
            with open("/tmp/crm_heartbeat_log.txt", "a") as f:
                f.write(f"{timestamp} GraphQL OK: {response.json()}\n")
        else:
            with open("/tmp/crm_heartbeat_log.txt", "a") as f:
                f.write(f"{timestamp} GraphQL ERROR: {response.status_code}\n")
    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{timestamp} GraphQL EXCEPTION: {str(e)}\n")
#-------------------------------

def update_low_stock():
    url = "http://localhost:8000/graphql"
    query = """
    mutation {
        updateLowStockProducts {
            message
            updatedProducts {
                name
                stock
            }
        }
    }
    """

    try:
        response = requests.post(url, json={'query': query})
        data = response.json()

        now = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        log_file = "/tmp/low_stock_updates_log.txt"

        with open(log_file, "a") as f:
            if "errors" in data:
                f.write(f"{now} ERROR: {data['errors']}\n")
            else:
                result = data["data"]["updateLowStockProducts"]
                f.write(f"{now} {result['message']}\n")

                for product in result["updatedProducts"]:
                    f.write(f"- {product['name']} new stock: {product['stock']}\n")

    except Exception as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            f.write(f"EXCEPTION {str(e)}\n")