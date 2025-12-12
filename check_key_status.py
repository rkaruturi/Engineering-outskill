import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print("Error: OPENROUTER_API_KEY not found in .env file.")
    exit(1)

print(f"Checking key: {api_key[:8]}...")

try:
    response = requests.get(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Key Information:")
        print(f"Label: {data.get('data', {}).get('label', 'Unknown')}")
        
        limit = data.get('data', {}).get('limit')
        usage = data.get('data', {}).get('usage')
        
        if limit is not None:
            print(f"Credit Limit: ${limit}")
        else:
            print("Credit Limit: Unlimited (or checking not supported)")
            
        if usage is not None:
             print(f"Usage: ${usage}")
        
        # Some keys might return exact credits
        credits = data.get('data', {}).get('credits')
        if credits is not None:
             print(f"Remaining Credits: ${credits}")
             
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"\n❌ Exception: {e}")
