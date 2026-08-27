import os
import base64
import pickle
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

class UserPreference:
    def __init__(self, username, theme="dark"):
        self.username = username
        self.theme = theme

@app.route('/')
def index():
    session_cookie = request.cookies.get('session_data')
    
    if session_cookie:
        try:
            decoded_data = base64.b64decode(session_cookie)
            user_pref = pickle.loads(decoded_data)
        except Exception as e:
            user_pref = UserPreference(username="Guest")
    else:
        user_pref = UserPreference(username="Guest")
    
    resp = make_response(render_template('index.html', user=user_pref))
    
    serialized_data = pickle.dumps(user_pref)
    encoded_data = base64.b64encode(serialized_data).decode('utf-8')
    resp.set_cookie('session_data', encoded_data)
    
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
