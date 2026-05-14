import sys
import os
import base64
import requests
import re

# MUST use environment variables for security! 
WAKATIME_API_KEY = os.environ.get('WAKATIME_API_KEY')
BASE_URL = 'https://wakatime.com/api/v1'
RANGE = 'all_time'
NUM_TOP_LANGUAGES = 5

CHAR_FULL = '■' 
CHAR_EMPTY = '□' 

BAR_WIDTH = 20     # Width of the bar
NAME_WIDTH = 10    # Max width of language name

IGNORED_LANGUAGES = ['Other', 'Fusion360', 'Fusion', 'Onshape', 'Text', 'JSON', 'YAML', 'Markdown', 'INI', 'XML', 'CAD', 'CSV', "Slack", "Chief Delphi", "Docs", "TeX"]

START_MARKER = "<!-- Stats Start -->"
END_MARKER = "<!-- Stats End -->"

def update_readme():
    if not WAKATIME_API_KEY:
        print("Error: WAKATIME_API_KEY environment variable not found.")
        sys.exit(1)

    try:
        print("Fetching stats...")
        encoded_key = base64.b64encode(WAKATIME_API_KEY.encode('utf-8')).decode('utf-8')
        headers = {'Authorization': f'Basic {encoded_key}'}
        response = requests.get(f'{BASE_URL}/users/current/stats/{RANGE}', headers=headers)
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            sys.exit(1)

        data = response.json()
        
        # Filter & Sort
        languages = data['data']['languages']
        filtered_languages = [l for l in languages if l['name'] not in IGNORED_LANGUAGES]
        filtered_languages.sort(key=lambda x: x['total_seconds'], reverse=True)
        top_languages = filtered_languages[:NUM_TOP_LANGUAGES]
        
        filtered_total_seconds = sum(l['total_seconds'] for l in filtered_languages)
        filtered_total_hours = filtered_total_seconds / 3600
        
        # Generate Markdown   
        stats_markdown = f"**All Time ({round(filtered_total_hours, 1)} Hours)**\n```text\n"
        for lang in top_languages:
            name = lang['name'][:NAME_WIDTH].ljust(NAME_WIDTH)
            percent = (lang['total_seconds'] / filtered_total_seconds * 100) if filtered_total_seconds > 0 else 0
            hours = lang['total_seconds'] / 3600
            
            bar_len = int(round((percent / 100) * BAR_WIDTH))
            bar = CHAR_FULL * bar_len + CHAR_EMPTY * (BAR_WIDTH - bar_len)
            
            stats_markdown += f"{name} {bar} {percent:.1f}% ({hours:.1f}h)\n"
            
        stats_markdown += "```\n"

        # Inject into README safely
        readme_path = 'README.md'
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if START_MARKER not in content or END_MARKER not in content:
            print(f"Error: Could not find start/end markers in {readme_path}.")
            sys.exit(1)

        # Use regex to replace only the text between the markers
        pattern = f"{START_MARKER}.*?{END_MARKER}"
        replacement = f"{START_MARKER}\n{stats_markdown}{END_MARKER}"
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("README updated successfully!")

    except Exception as e:
        print(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_readme()