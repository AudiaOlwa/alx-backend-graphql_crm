#!/usr/bin/env python3

import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

LOG_FILE = "/tmp/order_reminders_log.txt"

# GraphQL endpoint
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=False,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# Calculate date 7 days ago
seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()

query = gql("""
query GetRecentOrders($date: DateTime!) {
  orders(orderDate_Gte: $date) {
    id
    customer {
      email
    }
    orderDate
  }
}
""")

try:
    result = client.execute(query, variable_values={"date": seven_days_ago})
    orders = result.get("orders", [])

    with open(LOG_FILE, "a") as f:
        f.write(f"\n--- {datetime.now()} Order Reminder Run ---\n")
        for order in orders:
            log_msg = f"Order #{order['id']} | Email: {order['customer']['email']} | Date: {order['orderDate']}"
            print(log_msg)
            f.write(log_msg + "\n")

    print("Order reminders processed!")

except Exception as e:
    with open(LOG_FILE, "a") as f:
        f.write(f"Error on {datetime.now()}: {str(e)}\n")
    print("Error:", e)
