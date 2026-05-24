import json

def get_last_user_message():
    with open('C:/Users/T480S/.gemini/antigravity-ide/brain/450cd746-60ea-4028-b3e6-1fa0babc9c13/.system_generated/logs/transcript.jsonl', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in reversed(lines):
        if '"type":"USER_INPUT"' in line:
            data = json.loads(line)
            print(data['content'])
            break

if __name__ == '__main__':
    get_last_user_message()
