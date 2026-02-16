# pre_hash.py
import yaml
from streamlit_authenticator.utilities.hasher import Hasher

# 先手動寫你的原始 config（明文密碼）
config = {
    'credentials': {
        'usernames': {
            'ivan': {  # 你的使用者名稱
                'email': 'c.ch.ivan@hotmail.com',
                'name': 'Ivan_Chi',
                'password': 'Abcd1234'  # ← 這裡放明文密碼
            }
            # 可以加更多使用者
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'some_random_secret_key_please_change_this_1234567890',
        'name': 'mortgage_calculator_cookie'
    },
    'pre-authorized': {
        'emails': []
    }
}

# 自動 hash 所有明文密碼（這步會修改 config['credentials']）
Hasher.hash_passwords(config['credentials'])

# 輸出 hash 後的 config 到檔案
with open('config_hashed.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)

print("已產生 hashed config_hashed.yaml，請檢查並使用它！")
print("記得把原始明文 config 刪掉，不要上傳 GitHub")