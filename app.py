from flask import Flask, request, session, redirect, url_for, render_template
from pyArango.connection import Connection
from pyArango.collection import Collection
import hashlib

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Configuração do banco de dados ArangoDB
conn = Connection(username="root", password="rootpassword")
db = conn["todos"]

# Define uma coleção para usuários
if not db.hasCollection("users"):
    users = db.createCollection(name="users")
else:
    users = db["users"]

# Define uma coleção para tarefas
if not db.hasCollection("tasks"):
    tasks = db.createCollection(name="tasks")
else:
    tasks = db["tasks"]



@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        user_tasks = [{"_key": task._key, "task": task["task"]} for task in tasks.fetchByExample({"user": username}, batchSize=1)]
        return render_template('index.html', username=username, tasks=user_tasks)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        existing_user = users.fetchFirstExample({"username": username})
        if existing_user:
            return render_template('register.html', error_message='Username already exists!')
        else:
            users.createDocument({"username": username, "password": password}).save()
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        user = users.fetchFirstExample({"username": username})
        if user:
            if user[0]['password'] == password:
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error_message='Invalid password!')
        else:
            return render_template('login.html', error_message='User does not exist! Register below.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/save_task', methods=['POST'])
def save_task():
    if 'username' in session:
        username = session['username']
        task = request.form['task']
        tasks.createDocument({"user": username, "task": task}).save()
        return redirect(url_for('index'))
    else:
        return 'You are not logged in!'

@app.route('/delete_task/<task_key>', methods=['POST'])
def delete_task(task_key):
    if 'username' in session:
        username = session['username']
        task = tasks.fetchDocument(task_key)
        if task and task['user'] == username:
            task.delete()
        return redirect(url_for('index'))
    else:
        return 'You are not logged in!'

if __name__ == '__main__':
    app.run(debug=True)
