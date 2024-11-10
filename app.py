from flask import Flask, request, flash, redirect, url_for, render_template, session
import pymongo
import os
from bson.objectid import ObjectId

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['p-TaskSchedular']
task_collections = db['tasks']
user_collections = db['users']

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mysecretkey')

@app.route('/register', methods=['GET', 'POST'])
def register():
    err_user = None
    err_email = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        user = user_collections.find_one({'username': username})
        user_email = user_collections.find_one({'email': email})
        if user and user_email:
            err_user = "Username already exists"
            err_email = "Email is already used"
        elif user:
            err_user = "Username already exists"
        elif user_email:
            err_email = "Email is already used"
        else:
            user_collections.insert_one({'username': username, 'password': password, 'email': email})
            return redirect(url_for('login'))

    return render_template('register.html', err_user=err_user, err_email=err_email)

@app.route('/', methods=['GET', 'POST'])
def login():
    err = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = user_collections.find_one({'username': username})
        if user:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                session.permanent = True
                return redirect(url_for('dashboard'))
            else:
                err = "Invalid username or password"
        else:
            err = "Invalid username or password"

    return render_template('login.html', error=err)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('You need to log in first')
        return redirect(url_for('login'))

    tasks = list(task_collections.find({'username': session['username']}))
    return render_template('index.html', tasks=tasks)

@app.route('/addTask', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        scheduleTime = request.form['scheduleTime']

        try:
            task_collections.insert_one({
                'name': name,
                'description': description,
                'scheduleTime': scheduleTime,
                'status': 'pending',
                'username': session['username']
            })
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'An error occurred while adding the task: {str(e)}')
            return redirect(url_for('add_task'))
        
    return render_template('addTask.html')

@app.route('/editTask/<task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = task_collections.find_one({'_id': ObjectId(task_id)})
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        scheduleTime = request.form.get('scheduleTime')

        task_collections.update_one({'_id': ObjectId(task_id)}, {'$set': {
            'name': name,
            'description': description,
            'scheduleTime': scheduleTime
        }})
        return redirect(url_for('dashboard'))

    return render_template('editTask.html', task=task)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/deleteTask/<task_id>', methods=['POST'])
def delete_task(task_id):
    task_collections.delete_one({'_id': ObjectId(task_id)})
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)