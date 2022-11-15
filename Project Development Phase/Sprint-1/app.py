from  flask import Flask,render_template,url_for,request,flash,session,redirect
import ibm_db
from functools import wraps

app=Flask(__name__)
app.secret_key='ay'
try:
    conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=ba99a9e6-d59e-4883-8fc0-d6a8c9f7a08f.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=31321;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=hkl72011;PWD=EWU0l3XLa6KfY4Kf","","")
except:
    print("Unable to connect: ",ibm_db.conn_error())
    
@app.route('/')
def index():
    return render_template('Home.html')

@app.route("/Sign")
def Sign():
    return redirect(url_for("register"))

@app.route("/register",methods=['GET','POST'])
def register():
    error = None 
    if request.method=='POST':
           company=request.form['company'].title()
           location=request.form['location'].title()
           email=request.form['email']
           username=request.form['username']
           password=request.form['password']
           sql="SELECT * FROM REGISTER WHERE MAIL_ID=?"
           prep_stmt=ibm_db.prepare(conn,sql)
           ibm_db.bind_param(prep_stmt,1,email)
           ibm_db.execute(prep_stmt)
           account=ibm_db.fetch_assoc(prep_stmt)
           print(account)
           print(company)
           if account:
               error="Account already exists! Log in to continue !"
           else:
               insert_sql="INSERT INTO REGISTER (COMPANY,LOCATION,MAIL_ID,USER_ID,PASSWORD)values(?,?,?,?,?)"
               prep_stmt=ibm_db.prepare(conn,insert_sql)
               ibm_db.bind_param(prep_stmt,1,company)
               ibm_db.bind_param(prep_stmt,2,location)
               ibm_db.bind_param(prep_stmt,3,email)
               ibm_db.bind_param(prep_stmt,4,username)
               ibm_db.bind_param(prep_stmt,5,password)
               ibm_db.execute(prep_stmt)
               print("inserted")
               flash(" Registration successfull. Log in to continue !")
    else:
        print("not post")
        pass
    return render_template('Reg.html',error=error)

@app.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        sql="SELECT * FROM REGISTER WHERE USER_ID=? AND PASSWORD=?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            session['logged_in']=True
            session['id']=account['INVENTORY_ID']
            session["username"]=account["USER_ID"]
            flash("Logged in successfully!")
            return redirect(url_for("DashBoard"))
        else:
            error="Incorrect username / password"
            return render_template('Reg.html',error=error)
    else:
        pass
    return render_template('Reg.html',error=error)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Please login', 'info')
            return redirect(url_for('login'))
    return wrap
  
if __name__=='__main__':
    app.run(debug=True)