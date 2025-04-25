import base64
import requests

def create_midtrans_transaction(payload, server_key):
    auth_string = base64.b64encode(f"{server_key}:".encode()).decode()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_string}"
    }
    response = requests.post(
        url="https://app.sandbox.midtrans.com/snap/v1/transactions",
        # url="https://app.midtrans.com/snap/v1/transactions Sandbox
        headers=headers,
        json=payload
    )
    return response
