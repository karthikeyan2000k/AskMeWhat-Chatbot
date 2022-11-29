import re
import respond as res
from flask import Flask, render_template, request,session,logging,url_for,redirect,flash
from flask_recaptcha import ReCaptcha
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import mysql.connector
import os
import uuid
import bcrypt
from gtts import gTTS # google text to speech
import random
import playsound # to play an audio file

app = Flask(__name__)
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME'] = 'askmewhatchatbot@gmail.com'
app.config['MAIL_PASSWORD'] = 'collageproject@2021'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

bcrypt = Bcrypt(app)
mail=Mail(app)
recaptcha = ReCaptcha(app=app)
app.secret_key=os.urandom(24)
app.static_folder = 'static'


app.config.update(dict(
    RECAPTCHA_ENABLED = True,
    RECAPTCHA_SITE_KEY = "6LdbAx0aAAAAAANl04WHtDbraFMufACHccHbn09L",
    RECAPTCHA_SECRET_KEY = "6LdbAx0aAAAAAMmkgBKJ2Z9xsQjMD5YutoXC6Wee"
))

recaptcha=ReCaptcha()
recaptcha.init_app(app)




#database connectivity
conn=mysql.connector.connect(host='localhost',port='3306',user='root',password='root',database='register')
cur = conn.cursor(buffered=True)


# Google recaptcha - site key : 6LdbAx0aAAAAAANl04WHtDbraFMufACHccHbn09L
# Google recaptcha - secret key : 6LdbAx0aAAAAAMmkgBKJ2Z9xsQjMD5YutoXC6Wee

@app.route("/index")
def home():
    if 'id' in session:
        return render_template('index.html')
    else:
        return redirect('/')


@app.route('/')
def login():
    return render_template("login.html")

@app.route('/register')
def about():
    return render_template('register.html')

@app.route('/forgot',methods=['POST','GET'])
def forgot():
    if 'login' in session:
        return redirect('/')
    if request.method=="POST":
        email=request.form.get('email')
        token=str(uuid.uuid4())
        cur = conn.cursor(buffered=True)
        cur.execute("""SELECT * FROM `users` WHERE `email` LIKE '{}' """.format(email))
        users = cur.fetchone()
        if len(users)>0:
            msg=Message("Forgot password request",sender="askmewhatchatbot@gmail.com",recipients=[email])
            msg.body=render_template('sent.html',token=token,users=users)
            mail.send(msg)
            print(msg)
            cur.execute("UPDATE users SET token =%s WHERE email=%s",[token,email])
            flash("A mail has been sent.Check spam folders also",'success')
            conn.commit()
            cur.close()
            return redirect('/forgot')
        else:
            flash("Email do not match","danger")
            conn.commit()
            cur.close()
            return redirect('/forgot')
    return render_template('forgot.html')


        
@app.route('/acverify/<token>/<mailid>/<uname>/verify',methods=['POST','GET'])
def acverify(token,mailid,uname):
    session['emailofuser']=mailid
    session['username']=uname
    return render_template('/reregister.html')
@app.route('/reset/<token>',methods=['POST','GET'])
def reset(token):
    if 'login' in session:
        return redirect('/')
    if request.method=="POST":
        pword=request.form.get('pword')
        cpoword=request.form.get('copoword')
        tokentoken=str(uuid.uuid4())
        cur = conn.cursor(buffered=True)
        if pword!=cpoword:
            flash('Password do not match','danger')
            return redirect('reset')
        print(token)
        print(pword)
        cur.execute("SELECT * FROM users WHERE token =%s",[token])
        users = cur.fetchone()
        print(users)
        if len(users)>0:
            cur.execute("UPDATE users SET token =%s,password =%s WHERE token =%s",[tokentoken,pword,token] )
            conn.commit()
            cur.close()
            flash("Password successfully updated",'success')
            return redirect('/')
        else:
            flash("Token Invalid","danger")
            conn.commit()
            cur.close()
            return redirect('/')
    return render_template('reset.html')

@app.route('/login_validation',methods=['POST'])
def login_validation():
    email=request.form.get('email')
    password=request.form.get('password')

    cur.execute("""SELECT * FROM `users` WHERE `email` LIKE '{}' AND `password` LIKE '{}'""".format(email,password))
    users = cur.fetchall()
    if len(users)>0:
        session['id']=users[0][0]
        flash('You were successfully logged in')
        return redirect('/index')
    else:
        flash('Invalid credentials !!!')
        return redirect('/')
    # return "The Email is {} and the Password is {}".format(email,password)
    # return render_template('register.html')

@app.route('/add_user',methods=['POST'])
def add_user():
    name=request.form.get('name') 
    email=request.form.get('uemail')
    password=request.form.get('upassword')
    cur.execute("UPDATE users SET password='{}'WHERE name = '{}'".format(password, name))
    cur.execute("""INSERT INTO  users(name,email,password) VALUES('{}','{}','{}')""".format(name,email,password))
    conn.commit()
    cur.execute("""SELECT * FROM users WHERE email LIKE '{}'""".format(email))
    myuser=cur.fetchall()
    flash('You have successfully registered!')
    for i in myuser:
       print(i)
    session['id']=myuser[0]
   
    return redirect('/index')


@app.route('/suggestion',methods=['POST'])
def suggestion():
    email=request.form.get('uemail')
    suggesMess=request.form.get('message')

    cur.execute("""INSERT INTO  suggestion(email,message) VALUES('{}','{}')""".format(email,suggesMess))
    conn.commit()
    flash('You suggestion is succesfully sent!')
    return redirect('/index')

@app.route('/add_user',methods=['POST'])
def register():
    if recaptcha.verify():
        flash('New User Added Successfully')
        return redirect('/register')
    else:
        flash('Error Recaptcha') 
        return redirect('/register')


@app.route('/logout')
def logout():
    session.pop('id')
    return redirect('/')

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    split_message = re.split(r'\s+|[,;?!.-]\s*', userText.lower())
    response = check_all_messages(split_message)
    # read(response)
    return response

      

TAG_RE = re.compile(r'<[^>]+>')

def read(text):
 text=text.split('.')[0]   
 speak(TAG_RE.sub('',text))

def speak(audio_string):
    tts = gTTS(text=audio_string, lang='en') 
    r = random.randint(1,20000000)
    audio_file = 'audio.mp3'
    tts.save(audio_file) 
    playsound.playsound(audio_file)
    os.remove(audio_file)

def msg_score(user_message, recognised_words, single_response=False, must=[]):
    message_certainty = 0
    has_required_words = True

    
    for word in user_message:
        if word in recognised_words:
            message_certainty += 1

   
    percentage = float(message_certainty) / float(len(recognised_words))

    for word in must:
        if word not in user_message:
            has_required_words = False
            break

    if has_required_words or single_response:
        return int(percentage * 100)
    else:
        return 0


def check_all_messages(message):
    Scoreboard = {}

    # Simplifies response creation / adds it to the dict
    def response(bot_response, list_of_words, single_response=False, must=[]):
        nonlocal Scoreboard
        Scoreboard[bot_response] = msg_score(message, list_of_words, single_response, must)

    # Responses -------------------------------------------------------------------------------------------------------
    response('Hi I am here to answer any of your question regarding SASTRA University Please type in your Questions.', ['hello', 'hi', 'hey', 'sup', 'heyo'], single_response=True)
    response('See you!', ['bye', 'goodbye'], single_response=True)
    response('I\'m doing fine, and you?', ['how', 'are', 'you', 'doing'], must=['how'])
    response('You\'re welcome!', ['thank', 'thanks'], single_response=True)
    response('Can you mention which of the below admission information you are looking for.: 1 Engineering Admission 2 PG Admission 3 Law Admission 4 NRI Admission 5 Other Admissions',['admission','procedure','process','all'],must=['admission'])
    response(res.R_ADVICE, ['give', 'advice'], must=['advice'])
    response(res.R_EATING, ['what', 'you', 'eat'], must=['you', 'eat'])
    response(res.other_admissions,['procedure','arts','bsc','bcom','admission'],must=['admission'])
    response(res.engineering_admission,['process','btech','mtech','engineering','admission'],must=['admission'])
    response(res.PG_admission,['procedure','pg','admission'],must=['admission'])
    response(res.law_admission,['procedure','law','admission'],must=['admission'])
   
    response(res.nri_admission,['procedure','nri','admission'],must=['admission'])
    response(res.quota_availability,['seats','quota','reservation','availibility'],must=[])
    response(res.courses_offered,['course','courses','offered'],must=['courses'])
    response(res.foul_word,['stupid','idiot','fool'],must=[])
    response(res.contact_details,['contact','address','phone'],must=[])
    response(res.about_sastra,['tell','about','sastra','college'],must=['college','sastra'])
    response(res.fee_structure,['fee','fees','structure','cost','amount'],must=[])
    response(res.hostel_availability,['hostel'],must=[])
    response(res.student_web_interface,['student','login','portal','web','interface'],must=[])
    response(res.parent_web_interface,['parent','parents','web','interface','portal'],must=[])
    response(res.gym_facility,['gym'],must=[])
    response(res.badminton_facility,['badminton'],must=[])
    response(res.football_facility,['football'],must=[])
    response(res.cricket_facility,['cricket'],must=[])
    response(res.athletics_facility,['athletics'],must=[])
    response(res.swimming_facility,['swimming'],must=[])
    response(res.archery_facility,['archery'],must=[])
    response(res.tennis_facility,['tennis'],must=[])
    response(res.table_tennis_facility,['table','tennis'],must=[])
    response(res.basketball_facility,['basketball'],must=[])
    response(res.billiards_facility,['billiards'],must=[])
    response(res.carrom_facility,['carrom'],must=[])
    response(res.sports_facility,['sports'],must=[])
    response(res.library_facility,['library'],must=[])
    response(res.research_facility,['research'],must=[])
    response(res.wifi_facility,['wifi','internet'],must=[])
    response(res.canteen_facility,['canteen','food'],must=[])
    response(res.events,['events','festivals','fun'],must=[])
    response(res.cultural_events,['cultural','events','festival'],must=[])
    response(res.sport_events,['sport','events','festival'],must=[])
    response(res.technical_events,['technical','events','festival'],must=[])

    best_match = max(Scoreboard, key=Scoreboard.get)
    return res.unknown() if Scoreboard[best_match] < 1 else best_match

if __name__ == "__main__":
    # app.secret_key=""
    app.run() 
