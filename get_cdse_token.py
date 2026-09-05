import getpass
import requests

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

username = input("CDSE username/email: ")
password = getpass.getpass("CDSE password: ")

data = {
    "client_id": "cdse-public",
    "grant_type": "password",
    "username": username,
    "password": password,
}

response = requests.post(TOKEN_URL, data=data, timeout=60)

if response.status_code != 200:
    print("\nTOKEN REQUEST FAILED")
    print("HTTP:", response.status_code)
    print(response.text)
    raise SystemExit(1)

result = response.json()
access_token = result["access_token"]

with open("cdse_token.txt", "w", encoding="utf-8") as f:
    f.write(access_token)

print("\nTOKEN CREATED SUCCESSFULLY")
print("Token length:", len(access_token))
print("Saved: cdse_token.txt")