import requests

r = requests.get("http://54.215.190.254:5000")
print(r.json())