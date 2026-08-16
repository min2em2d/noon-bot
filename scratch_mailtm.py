import requests
import random
import string
import time

def test_mail_tm():
    session = requests.Session()
    
    # 1. Get Domains
    url_domains = "https://api.mail.tm/domains"
    resp = session.get(url_domains).json()
    print("Available domains:", resp)
    domain = resp["hydra:member"][0]["domain"]
    
    # 2. Generate Account Details
    username = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    address = f"{username}@{domain}"
    password = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
    
    print(f"Creating account: {address} with password: {password}")
    
    # 3. Create Account
    url_accounts = "https://api.mail.tm/accounts"
    resp_create = session.post(url_accounts, json={"address": address, "password": password})
    print("Create Account Status:", resp_create.status_code)
    print("Create Account Response:", resp_create.text)
    
    if resp_create.status_code != 201:
        print("Failed to create account")
        return
        
    # 4. Get Auth Token
    url_token = "https://api.mail.tm/token"
    resp_token = session.post(url_token, json={"address": address, "password": password}).json()
    token = resp_token["token"]
    print("JWT Token acquired:", token[:20] + "...")
    
    # 5. Check mailbox
    headers = {"Authorization": f"Bearer {token}"}
    url_messages = "https://api.mail.tm/messages"
    resp_msgs = session.get(url_messages, headers=headers).json()
    print("Messages inside inbox:", resp_msgs)

if __name__ == "__main__":
    test_mail_tm()
