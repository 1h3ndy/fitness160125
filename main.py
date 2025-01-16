from flask import Flask, render_template, session, redirect, url_for, request, flash
import sqlite3
from markupsafe import escape

from datetime import datetime, timedelta

exercises_dict = {
    'Bench Press': 'Chest',
    'Incline Bench Press': 'Chest',
    'Chest Fly': 'Chest',
    'Squat': 'Legs',
    'Lunge': 'Legs',
    'Leg Press': 'Legs',
    'Pull-Up': 'Back',
    'Deadlift': 'Back',
    'Barbell Row': 'Back',
    'Shoulder Press': 'Shoulders',
    'Lateral Raise': 'Shoulders',
    'Arnold Press': 'Shoulders',
    'Bicep Curl': 'Arms',
    'Tricep Extension': 'Arms',
    'Hammer Curl': 'Arms'
} # make createworkout.html pull from here

app = Flask(__name__)
#permanent = True
#session.permanent_session_lifetime = timedelta(hours = 24)


with sqlite3.connect('login.db') as db:
    db.execute("PRAGMA foreign_keys = ON")




@app.route('/')
def home():
   
    if 'username' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/login')
def login():
  
    return render_template('login.html')

@app.route('/signup')
def signup():

    return render_template('signup.html')



#c
@app.route('/add', methods=['POST']) # updated add for new database schema
def add():
    if request.form['password'] != request.form['psw-repeat']:
        flash("Passwords ")
        return redirect(url_for('login'))  #
    with sqlite3.connect('login.db') as db:
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO User (Name, Email, Password, Height, Weight, Age, Sex)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form['username'],
                request.form['email'],
                request.form['password'],  # we shoud encrypt
                request.form.get('height', None),
                request.form.get('weight', None),
                request.form.get('age', None),
                request.form.get('sex', None),

            ))
            db.commit()
            flash(f"User '{request.form['username']}' added successfully!")
            return redirect(url_for('home'))
        except Exception as e: # let them kno its taken

            flash("An error has occured")
            return redirect(url_for('login'))


@app.route('/verify', methods=['POST'])
def verify():
   #ddd
    with sqlite3.connect('login.db') as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM User WHERE Name=? AND Password=?",
                       (request.form['username'], request.form['password']))
        result = cursor.fetchall()
        if len(result) == 0:
            return 'Username or password not recognized.'
        else:
            session.permanent = True
            session['username'] = request.form['username']
             #get email also unless we force usernames to be unique
            return redirect(url_for('home'))  



@app.route('/un')
def un():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in.'

@app.route('/logout')
def logout():
    
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/create_workout')
def createworkout():
    if 'username' not in session: # ion my testing just becuase theres a username in session inst very good security, change
        return redirect(url_for('login'))
    return render_template('create_workout.html')

@app.route('/my_workouts')
def myworkouts():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('my_workouts.html')














## api section, mabe seperate file .
@app.route('/create-workout/submit', methods=['POST'])
def create_workout_submit():
    if 'username' not in session:
        return redirect(url_for('login'))
    print("session useranem:" + session['username'])

    username = session['username']
    with sqlite3.connect('login.db') as db: # we need to connect with foregn keeys enabled always, FIXES BUG WHERE STUFF DOESNT AUTOINCREMENT
        cursor = db.cursor()
        cursor.execute("SELECT User_ID FROM User WHERE Name = ?", (username,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        user_id = user[0]

        cursor.execute("""
            INSERT INTO Workouts (User_ID, Date, Field) VALUES (?, DATE('now'), 'General')
        """, (user_id,))
        workout_id = cursor.lastrowid
        exercises = zip(
            request.form.getlist('name[]'),
            request.form.getlist('sets[]'),
            request.form.getlist('reps[]'),
            request.form.getlist('weight[]')
        )

        for name, sets, reps, weight in exercises:
            cursor.execute("""
                INSERT INTO Exercise (Workout_ID, Exercise_Name, No_Sets, No_Reps_Per_Set, Weight)
                VALUES (?, ?, ?, ?, ?) 
            """, (workout_id, name, sets, reps, weight))#question mark is %s
        db.commit()

    return redirect(url_for('myworkouts'))


@app.route('/api/get-workouts', methods=['GET'])
def get_workouts_api():
    if 'username' not in session:
        return {"message": "Unauthorized"}, 401

    username = session['username']

    with sqlite3.connect('login.db') as db:

        cursor = db.cursor()


        cursor.execute("SELECT User_ID FROM User WHERE Name = ?", (username,))
        user = cursor.fetchone()
        if not user:
            return {"message": "User not found"}, 404
        user_id = user[0]


        cursor.execute("""
            SELECT 
                Workouts.Date, 
                Exercise.Exercise_Name, 
                Exercise.No_Sets, 
                Exercise.No_Reps_Per_Set, 
                Exercise.Weight
            FROM Workouts
            JOIN Exercise ON Workouts.Workout_ID = Exercise.Workout_ID
            WHERE Workouts.User_ID = ?
            ORDER BY Workouts.Date DESC
        """, (user_id,))
        workouts = cursor.fetchall()
    formatworkouts = [
        {
            "date": row[0],
            "exercise": row[1],
            "sets": row[2],
            "reps": row[3],
            "weight": row[4]
        }
        for row in workouts
    ]

    return {"workouts": formatworkouts}, 200



app.secret_key = 'the random string'
app.run(port=5021, debug=True)
