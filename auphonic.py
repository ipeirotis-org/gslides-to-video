# @title Cleanup the audio

import requests
from requests.auth import HTTPBasicAuth

# Set API endpoint, username, and password
api_endpoint = 'https://auphonic.com/api/simple/productions.json'
username = auphonic_username
password = auphonic_password

# Set up form data
form_data = {
    'preset': '9ZtYvnEGWqv3VD7373fU4D',
    'title': 'Clean up video narrative',
    'action': 'start'
}

# Specify the input file
files = {'input_file': ('slide_1.mp3', open('/content/slides/output/F-SQL_Subqueries-7.2/slide_1.mp3', 'rb'))}

# Make the POST request
response = requests.post(
    api_endpoint,
    auth=HTTPBasicAuth(username, password),
    data=form_data,
    files=files
)

# Output the response
print(response.json())
