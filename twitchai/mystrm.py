# mystrm.py
import requests

def send_message_via_mystrm(token: str, message: str, api_url: str):
    if not message.strip():
        return False
    try:
        resp = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"message": message.strip()},
            timeout=10
        )
        if resp.status_code == 200:
            print(f"✅ Отправлено через MyStrm: {message[:50]}...")
            return True
        else:
            print(f"❌ Ошибка MyStrm: {resp.status_code} — {resp.text}")
            return False
    except Exception as e:
        print(f"❗ Ошибка отправки в MyStrm: {e}")
        return False