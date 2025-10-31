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
