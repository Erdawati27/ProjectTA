from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
from datetime import date
import re
import mysql.connector
from flask_mysqldb import MySQL
import cv2
import numpy as np
import os
import time
from user import User
from facereg import FaceReg
from person import Person
from accs import Acces
from Image import Image


UPLOAD_FOLDER = 'dataset'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'buta_db'

Mysql = MySQL(app)
cnt = 0
pause_cnt = 0
justscanned = False

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="buta_db"
)
mycursor = mydb.cursor()

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'id' in session:
        return redirect('/dashboard')
    else:
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            user = User.get_by_username(username, Mysql)

            if user and user.check_password(password):
                # login successful
                session['loggedin'] = True
                session['id'] = user.id_user
                session['username'] = user.username
                msg = 'Logged in successfully !'
                return redirect('/dashboard')
            else:
                # login failed
                return render_template('login.html', error='Invalid username or password')
    return render_template('login.html', msg=msg)


@app.route('/logout')

def logout():
    if 'id' in session:
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        return redirect(url_for('login'))
    else:
        return redirect('/dashboard')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'id' in session:
        return redirect('/dashboard')
    else:
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            account = User.get_by_username(username,Mysql)
            if account:
                msg = 'Account already exists !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address !'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers !'
            elif not username or not password or not email:
                msg = 'Please fill out the form !'
            else:
                hashPsw=generate_password_hash(password, method='sha256')
                data = User('',username, hashPsw, email, Mysql)
                data.register()
                msg = 'You have successfully registered !'
                return render_template('login.html', msg=msg)
        elif request.method == 'POST':
            msg = 'Please fill out the form !'
        return render_template('register.html', msg=msg)



# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Generate dataset >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def generate_dataset(nbr):
    face_classifier = cv2.CascadeClassifier(
        "C:/Users/ASUS-JM/PycharmProjects/pythonProject/resources/haarcascade_frontalface_default.xml")

    def face_cropped(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        # scaling factor=1.3
        # Minimum neighbor = 5

        if faces is ():
            return None
        for (x, y, w, h) in faces:
            cropped_face = img[y:y + h, x:x + w]
        return cropped_face

    cap = cv2.VideoCapture(0)

    mycursor.execute("select ifnull(max(img_id), 0) from img_dataset")
    row = mycursor.fetchone()
    lastid = row[0]

    img_id = lastid
    max_imgid = img_id + 100
    count_img = 0

    while True:
        ret, img = cap.read()
        if face_cropped(img) is not None:
            count_img += 1
            img_id += 1
            face = cv2.resize(face_cropped(img), (200, 200))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

            file_name_path = "static/dataset/" + nbr + "." + str(img_id) + ".jpg"
            cv2.imwrite(file_name_path, face)
            cv2.putText(face, str(count_img), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

            mycursor.execute("""INSERT INTO `img_dataset` (`img_id`, `img_person`) VALUES
                                ('{}', '{}')""".format(img_id, nbr))
            mydb.commit()

            frame = cv2.imencode('.jpg', face)[1].tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            if cv2.waitKey(1) == 13 or int(img_id) == int(max_imgid):
                break
                cap.release()
                cv2.destroyAllWindows()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Train Classifier >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route('/train_classifier/<nbr>')
def train_classifier(nbr):
    dataset_dir = "C:/Users/ASUS-JM/PycharmProjects/pythonProject/static/dataset"

    path = [os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir)]
    faces = []
    ids = []

    for image in path:
        img = Image.open(image).convert('L');
        imageNp = np.array(img, 'uint8')
        id = int(os.path.split(image)[1].split(".")[1])

        faces.append(imageNp)
        ids.append(id)
    ids = np.array(ids)

    # Train the classifier and save
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    clf.write("classifier.xml")

    return redirect('/dashboard')

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Face Recognition >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def face_recognition():  # generate frame by frame from camera
    def draw_boundary(img, classifier, scaleFactor, minNeighbors, color, text, clf):
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        features = classifier.detectMultiScale(gray_image, scaleFactor, minNeighbors)

        global justscanned
        global pause_cnt

        pause_cnt += 1

        coords = []

        for (x, y, w, h) in features:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            id, pred = clf.predict(gray_image[y:y + h, x:x + w])
            confidence = int(100 * (1 - pred / 300))

            if confidence > 70 and not justscanned:
                global cnt
                cnt += 1

                n = (100 / 30) * cnt
                # w_filled = (n / 100) * w
                w_filled = (cnt / 30) * w

                cv2.putText(img, str(int(n)) + ' %', (x + 20, y + h + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (153, 255, 255), 2, cv2.LINE_AA)

                cv2.rectangle(img, (x, y + h + 40), (x + w, y + h + 50), color, 2)
                cv2.rectangle(img, (x, y + h + 40), (x + int(w_filled), y + h + 50), (153, 255, 255), cv2.FILLED)

                mycursor.execute("select a.img_person, b.prs_name, b.prs_address,b.prs_no_hp "
                                 "  from img_dataset a "
                                 "  left join prs_mstr b on a.img_person = b.prs_nbr "
                                 " where img_id = " + str(id))
                row = mycursor.fetchone()
                pnbr = row[0]
                pname = row[1]
                # pskill = row[2]

                if int(cnt) == 30:
                    cnt = 0
                    dateNow = date.today()
                    data = FaceReg(dateNow, pnbr, Mysql,app)
                    data.RecAccs()
                    # mycursor.execute("insert into accs_hist (accs_date, accs_prsn) values('" + str(
                    #     date.today()) + "', '" + pnbr + "')")
                    # mydb.commit()

                    cv2.putText(img, pname, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                                (153, 255, 255), 2, cv2.LINE_AA)
                    time.sleep(1)

                    justscanned = True
                    pause_cnt = 0

            else:
                if not justscanned:
                    cv2.putText(img, 'UNKNOWN', (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
                else:
                    cv2.putText(img, ' ', (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

                if pause_cnt > 80:
                    justscanned = False

            coords = [x, y, w, h]
        return coords

    def recognize(img, clf, faceCascade):
        coords = draw_boundary(img, faceCascade, 1.1, 10, (255, 255, 0), "Face", clf)
        return img

    faceCascade = cv2.CascadeClassifier(
        "C:/Users/ASUS-JM/PycharmProjects/pythonProject/resources/haarcascade_frontalface_default.xml")
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("classifier.xml")

    wCam, hCam = 400, 400

    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    while True:
        ret, img = cap.read()
        img = recognize(img, clf, faceCascade)

        frame = cv2.imencode('.jpg', img)[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

        key = cv2.waitKey(1)
        if key == 27:
            break



@app.route('/dashboard')
def home():
    if 'id' in session:
        data = Acces.get_list_accs(Mysql)
        return render_template('index.html', data=data)
    else:
        return redirect('/login')

@app.route('/list-person')
def list_person():
    data = Person.list_prsn(Mysql)
    return render_template('listprsn.html', data=data)

@app.route('/detail-person/<id>')
def detail_person(id):
    data = Person.get_prsn(id,Mysql)
    imgs = Image.get_img(str(id),Mysql)
    nameImg = str(imgs[0][1]) + '.' + str(imgs[0][0]) + '.jpg'
    img = nameImg
    return render_template('detailprsn.html', data=data,img=img)

@app.route('/lihat/<id>')
def lihat(id):
    data = Acces.get_accs_data(id,Mysql)
    imgs = Image.get_img(str(data[1]),Mysql)
    nameImg = str(imgs[0][1]) + '.' + str(imgs[0][0]) + '.jpg'
    img = nameImg
    return render_template('detail.html', data=data,img=img)

dataDet = []
@app.route('/fr_detail/<id>')
def fr_detail(id):
    data = Acces.get_accs_data(id, Mysql)
    imgs = Image.get_img(str(data[1]), Mysql)
    nameImg = str(imgs[0][1]) + '.' + str(imgs[0][0]) + '.jpg'
    img = nameImg
    return render_template('fr_detail.html', data=data,img=img,id=id)

@app.route('/display/<filename>')
def display_image(filename):
	return redirect(url_for('dataset', filename= filename))


@app.route('/addprsn')
def addprsn():
    mycursor.execute("select ifnull(max(prs_nbr) + 1, 101) from prs_mstr")
    row = mycursor.fetchone()
    nbr = row[0]
    # print(int(nbr))

    return render_template('addprsn.html', newnbr=int(nbr))


@app.route('/addprsn_submit', methods=['POST'])
def addprsn_submit():
    prsnbr = request.form.get('txtnbr')
    prsname = request.form.get('txtname')
    prsaddress = request.form.get('address')
    prsphone= request.form.get('phone')
    prstujuan = request.form.get('tujuan')

    prsn= Person(prsnbr,prsname,prsaddress,prsphone,'','',Mysql)
    prsn.add()

    acs = Acces('',str(date.today()),prsnbr,'',prstujuan,Mysql)
    acs.recAccs()
    return redirect(url_for('vfdataset_page', prs=prsnbr))

@app.route('/editprsn_submit', methods=['POST'])
def editprsn_submit():
    idAcc = request.form.get('idAcc')
    prsid = request.form.get('txtid')
    prstujuan = request.form.get('tujuan')
    id = str(idAcc)
    row = Acces.select_date(id,Mysql)
    data = Acces(idAcc,row[0],prsid,row[1],prstujuan,Mysql)
    data.update_accs()

    return redirect(url_for('home'))


@app.route('/vfdataset_page/<prs>')
def vfdataset_page(prs):
    return render_template('addprsn.html', prs=prs)


@app.route('/vidfeed_dataset/<nbr>')
def vidfeed_dataset(nbr):
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(generate_dataset(nbr), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed')
def video_feed():
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(face_recognition(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/fr_page')
def fr_page():
    """Video streaming home page."""
    return render_template('fr_page.html')


@app.route('/countTodayScan')
def countTodayScan():
    cur = Mysql.connection.cursor()
    cur.execute("select count(*) "
                     "  from accs_hist "
                     " where accs_date = curdate() ")
    row = cur.fetchone()
    rowcount = row[0]

    return jsonify({'rowcount': rowcount})

@app.route('/loadLastData', methods=['GET', 'POST'])
def loadLastData():
    cur = Mysql.connection.cursor()
    cur.execute("select a.accs_id, a.accs_prsn, b.prs_name, b.prs_address, b.prs_no_hp,date_format(a.accs_date, '%D:%M:%Y'), date_format(a.accs_added, '%H:%i:%s') "
                     "  from accs_hist a "
                     "  left join prs_mstr b on a.accs_prsn = b.prs_nbr "
                     " where a.accs_date = curdate() "
                     " order by accs_id desc limit 1")
    data = cur.fetchall()

    return jsonify(data=data)

@app.route('/hapusprsn/<id>', methods=['GET'])
def hapusprsn(id):
    cur = Mysql.connection.cursor()
    cur.execute("DELETE FROM prs_mstr WHERE prs_nbr = "+id)
    Mysql.connection.commit()
    data = Person.list_prsn(Mysql)

    return render_template('listprsn.html', data=data)

@app.route('/hapushst/<id>', methods=['GET'])
def hapushst(id):
    cur = Mysql.connection.cursor()
    cur.execute("DELETE FROM accs_hist WHERE accs_id = "+id)
    Mysql.connection.commit()
    data = Acces.get_list_accs(Mysql)

    return render_template('index.html', data=data)

if __name__ == "__main__":
    app.secret_key = 'GJHJGGJJ&**&GFHF^%FYTFFI&O*F&f7ff7rf7fuygu'
    app.config['SESSION_TYPE'] = 'memcached'
    app.run(host='127.0.0.1', port=8000, debug=True)
