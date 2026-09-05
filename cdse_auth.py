import requests
import getpass

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

username = input("Enter your Copernicus Data Space username/email: ")
password = getpass.getpass("Enter your Copernicus Data Space password: ")

data = {
    "client_id": "cdse-public",
    "username": username,
    "password": password,
    "grant_type": "password",
}

print()
print("Authenticating with Copernicus Data Space...")

response = requests.post(
    TOKEN_URL,
    data=data,
    timeout=60
)

print("HTTP status:", response.status_code)

if response.status_code != 200:
    print()
    print("Authentication failed:")
    print(response.text)
    raise SystemExit(1)

token = response.json()["access_token"]

with open("cdse_token.txt", "w", encoding="utf-8") as f:
    f.write(token)

print()
print("=" * 60)
print("AUTHENTICATION SUCCESSFUL")
print("=" * 60)
print("Token saved locally to cdse_token.txt")