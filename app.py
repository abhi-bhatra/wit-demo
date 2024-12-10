from flask import Flask, request, render_template_string, redirect, session, send_file
import sqlite3

app = Flask(__name__)
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
<html>
    <h1>Welcome {{name}}!</h1>
    <form method="POST" action="/login">
        Username: <input type="text" name="username"><br>
        Password: <input type="text" name="password"><br>
        <input type="submit" value="Login">
    </form>
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
    
    # Vulnerable: XSS through direct HTML rendering
    return f"""
    <h1>Dashboard</h1>
    <p>Welcome {session['username']}!</p>
    <h2>Your Notes:</h2>
    {notes}
    <form method="POST">
        <textarea name="note">{notes}</textarea>
        <input type="submit" value="Save Note">
    </form>
    <a href="/logout">Logout</a>
    """

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)  # Vulnerable: Debug mode enabled in production
