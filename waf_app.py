from flask import Flask, request, Response, redirect
import re
import requests

app = Flask(__name__)

# Target ASP.NET site (update with your actual target URL)
TARGET_URL = 'https://localhost:44330/01LoginPage.aspx'  # Change to protect 01LoginPage.aspx

# XSS detection pattern (matches <script> tags and alert() calls)
xss_pattern = re.compile(r'<script.*?>.*?</script>|alert\((.*?)\)', re.IGNORECASE)

# Get the IP like a pro
def get_ip():
    """Get the IP address of the client making the request."""
    return request.remote_addr

# Function to check if input contains XSS
def is_xss_safe(user_input):
    if xss_pattern.search(user_input):
        return False
    return True

@app.route('/01LoginPage.aspx', methods=['GET', 'POST'])  # Protecting the login page now
def proxy_site():
    print("Incoming request to /01LoginPage.aspx")
    
    try:
        # Check GET request for XSS (in query params)
        user_input = request.args.get('user_input', '')
        print(f"GET user_input: {user_input}")
        if user_input and not is_xss_safe(user_input):
            print("Potential XSS detected in GET request!")
            return "Potential XSS attack detected!", 400

        # Check POST request for XSS (in form data: txtUsername and txtPassword)
        if request.method == 'POST':
            # Check username and password input for XSS
            username = request.form.get('txtUsername', '')
            password = request.form.get('txtPassword', '')
            print(f"POST username: {username}, password: {password}")
            if not is_xss_safe(username) or not is_xss_safe(password):
                print(f"Potential XSS detected in POST request! {get_ip()}")
                return f"Potential XSS attack detected! {get_ip()}", 400

            # Check if any part of the alert script or XSS in response is detected (error message)
            if 'alert' in request.form.get('btnSubmit', ''):
                print("Potential XSS detected in button submission!")
                return "Potential XSS attack detected!", 400

        # If input is safe, forward the request to the target ASP.NET site
        if request.method == 'GET':
            resp = requests.get(TARGET_URL, params=request.args, verify=False)
        else:
            resp = requests.post(TARGET_URL, data=request.form, verify=False)

        # Check if the response contains static resource URLs (like CSS)
        if 'text/html' in resp.headers['Content-Type']:
            # Check if any static resources (like CSS) need to be decoded
            html_content = resp.content.decode('utf-8')
            # Rewrite the link to the correct path for your CSS file (handle absolute/relative links)
            html_content = html_content.replace('href="10LoginStyle.css"', 'href="/static/10LoginStyle.css"')
            html_content = html_content.replace('src="Images/The_Krusty_Krab.png"', 'src="/static/The_Krusty_Krab.png"')
            return Response(html_content, status=resp.status_code, content_type='text/html')
        
        
        # Forward the response from the target site
        return Response(resp.content, status=resp.status_code, content_type=resp.headers['Content-Type'])

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Internal Server Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc', port=5000)   # Running on https://localhost:5000
