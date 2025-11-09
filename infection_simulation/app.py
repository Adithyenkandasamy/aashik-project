from flask import Flask, render_template, request, redirect, url_for, session, flash
from collections import deque

app = Flask(__name__)
app.secret_key = "supersecretkey"  # for session handling

# ---------- GLOBAL VARIABLES ----------
MAX = 20
users = {}  # {username: password}
logged_in_user = None


# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']

    if username in users:
        flash("Username already exists!")
        return redirect(url_for('home'))

    users[username] = password
    flash("Signup successful! You can now login.")
    return redirect(url_for('home'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in users and users[username] == password:
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password.")
        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.")
    return redirect(url_for('home'))


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html')


@app.route('/simulate', methods=['POST'])
def simulate():
    if 'username' not in session:
        return redirect(url_for('home'))

    try:
        n = int(request.form['n'])
        region_names = [name.strip() for name in request.form['region_names'].split(',')]
        
        # Parse connections more robustly
        connections = []
        connection_strings = [c.strip() for c in request.form['connections'].split(',')]
        for conn_str in connection_strings:
            if conn_str:  # Skip empty strings
                parts = conn_str.split('-')
                if len(parts) != 2:
                    raise ValueError(f"Invalid connection format: '{conn_str}'. Use format like '0-1'")
                connections.append((int(parts[0]), int(parts[1])))
        
        infected_sources = [int(s.strip()) for s in request.form['infected_sources'].split(',') if s.strip()]
    except ValueError as e:
        flash(f"Invalid input format: {str(e)}")
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash("Invalid input format! Please check your data.")
        return redirect(url_for('dashboard'))

    # Input validation
    if n <= 0 or n > MAX:
        flash("Invalid number of regions! Must be between 1 and 20.")
        return redirect(url_for('dashboard'))
    
    if len(region_names) != n:
        flash(f"Number of region names ({len(region_names)}) must match number of regions ({n})!")
        return redirect(url_for('dashboard'))
    
    # Validate connections
    for u, v in connections:
        if not (0 <= u < n and 0 <= v < n):
            flash(f"Invalid connection {u}-{v}! Region indices must be between 0 and {n-1}.")
            return redirect(url_for('dashboard'))
    
    # Validate infected sources
    for src in infected_sources:
        if not (0 <= src < n):
            flash(f"Invalid infected source {src}! Region indices must be between 0 and {n-1}.")
            return redirect(url_for('dashboard'))

    # Initialize graph
    graph = [[0] * n for _ in range(n)]
    for u, v in connections:
        if 0 <= u < n and 0 <= v < n:
            graph[u][v] = 1
            graph[v][u] = 1

    # BFS Infection Simulation
    infected = [0] * n
    time = [-1] * n
    q = deque()

    for src in infected_sources:
        if 0 <= src < n:
            q.append(src)
            infected[src] = 1
            time[src] = 0

    timeline = []
    while q:
        region = q.popleft()
        timeline.append((region_names[region], time[region]))
        for i in range(n):
            if graph[region][i] == 1 and infected[i] == 0:
                infected[i] = 1
                time[i] = time[region] + 1
                q.append(i)

    # Safe regions
    safe_regions = [region_names[i] for i in range(n) if infected[i] == 0]

    return render_template('result.html', timeline=timeline, safe_regions=safe_regions)


if __name__ == '__main__':
    app.run(debug=True)
