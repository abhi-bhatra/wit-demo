from flask import Flask, request, render_template_string, redirect, session, send_file
import sqlite3

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'YOUR_UNIQUE_AND_SECRET_KEY_HERE'

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT, password TEXT, notes TEXT)''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, password, "Welcome!"))
    conn.commit()
    conn.close()

# Initialize with a default user
init_db()
add_user("admin", "admin123")

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Notes - Login</title>
    <link href="/static/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            padding-top: 50px;
        }
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .login-header {
            text-align: center;
            margin-bottom: 25px;
            color: #343a40;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="login-container">
            <div class="login-header">
                <h1 class="h3">Welcome {{name}}!</h1>
                <p class="text-muted">Please sign in to access your notes</p>
            </div>
            <form method="POST" action="/login">
                <div class="mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" class="form-control" id="username" name="username" required>
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Password</label>
                    <input type="text" class="form-control" id="password" name="password" required>
                </div>
                <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-primary">Login</button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
"""

# Vulnerable: SQL Injection possible
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Vulnerable: SQL injection possible here
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        result = c.execute(query).fetchone()
        conn.close()

        if result:
            session['username'] = username
            return redirect('/dashboard')
    
    return render_template_string(LOGIN_TEMPLATE, name="Guest")

# Vulnerable: Directory traversal
@app.route('/download')
def download_file():
    filename = request.args.get('file')
    # Vulnerable: No path validation
    return send_file(filename, as_attachment=True)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        note = request.form.get('note', '')
        c.execute("UPDATE users SET notes=? WHERE username=?", (note, session['username']))
        conn.commit()
    
    # Fetch user's notes
    result = c.execute("SELECT notes FROM users WHERE username=?", (session['username'],)).fetchone()
    notes = result[0] if result else ""
    conn.close()
    
    # Improved UI for dashboard while maintaining the same functionality
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Secure Notes - Dashboard</title>
        <link href="/static/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                background-color: #f8f9fa;
                padding: 20px;
            }}
            .dashboard-container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
                padding: 25px;
            }}
            .notes-area {{
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
                border-left: 4px solid #0d6efd;
            }}
            .header-bar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 1px solid #e9ecef;
            }}
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <div class="header-bar">
                <h1 class="h3">Notes Dashboard</h1>
                <div>
                    <span class="badge bg-success">Logged in as {session['username']}</span>
                    <a href="/logout" class="btn btn-outline-danger btn-sm ms-2">Logout</a>
                </div>
            </div>
            
            <h2 class="h4 mb-3">Your Notes</h2>
            <div class="notes-area">
                {notes}
            </div>
            
            <form method="POST">
                <div class="mb-3">
                    <label for="note" class="form-label">Edit Your Notes:</label>
                    <textarea name="note" id="note" class="form-control" rows="6">{notes}</textarea>
                </div>
                <button type="submit" class="btn btn-primary">Save Note</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)  # Vulnerable: Debug mode enabled in production
