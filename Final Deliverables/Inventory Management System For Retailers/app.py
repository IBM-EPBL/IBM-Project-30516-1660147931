from  flask import Flask,render_template,url_for,request,flash,session,redirect
import ibm_db
import re
from functools import wraps
from tabulate import tabulate
import configparser
import ssl
ssl._create_default_https_context=ssl._create_unverified_context
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

config=configparser.ConfigParser()
config.read("config.ini")

try:
    settings=config["SETTINGS"]
except:
    settings={}

app=Flask(__name__)
app.secret_key='ay'
try:
    conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=ba99a9e6-d59e-4883-8fc0-d6a8c9f7a08f.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=31321;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=hkl72011;PWD=EWU0l3XLa6KfY4Kf","","")
except:
    print("Unable to connect: ",ibm_db.conn_error())

 
regex_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

API=settings.get("APIKEY",None)
from_email=settings.get("FROM",None)

def sendmail(API,from_email,to_emails,subject,html_content):
   #if API!=None and from_email!=None and len(to_emails)>0:
        message=Mail(from_email,to_emails,subject,html_content)
        print(message)
        try:
            sg = SendGridAPIClient(API)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)

def alert(pro_id,pro_grp,pro_name,Tot_Q,Available,Shipped,Minimum_stock,Supplier):
    if Available<Minimum_stock:
        to_email=session['company_mail']
        subject="Your Product Stock Is Low"
        html_content='''Hi '''+session["username"]+''',
        Your product is less than minimum stock for the product '''+pro_name+'''

        Description:
        Product ID:'''+pro_id+'''
        Product Group:'''+pro_grp+'''
        Product Name:'''+pro_name+'''
        Total Quantity:'''+Tot_Q+'''
        Available:'''+Available+'''
        Shipped:'''+Shipped+'''
        Minimum_stock:'''+Minimum_stock+'''
        Supplier:'''+Supplier+'''

        Regards,
        IStock'''
        sendmail(API,from_email,to_email,subject,html_content)
        print("alert sent ")
        return "Mail Sent"
    else:
        return "Mail Not Sent"

def sendreportmail():
    count()
    list_pro=[]
    list_sup=[]
    list_pro=procount()
    list_sup=supcount()
    print(tabulate(list_pro))
    to_email=session['company_mail']
    subject="Your Inventory Report"
    content_first='''Hi '''+str(session["username"])+''',
    Total Products: '''+str(session['total_pro'])+'''
    Total Supplier: '''+str(session['total_sup'])+'''
    Minimum Stock: '''+str(session['total_min'])
    content_second='''
    Product Details:
    '''+tabulate(list_pro)+'''
    Supplier Details:
    '''+tabulate(list_sup)+'''

    Regards,
    IStock'''
    html_content=content_first+content_second
    sendmail(API,from_email,to_email,subject,html_content)


'''def forgot():
    OTP = [5461,3254,7485,4521,7496,3201,2058,7485,9647,3096,7804,9640]
    random_otp = random.choice(OTP)
    to_email=session['company_mail']
    subject="OTP"
    html_content="OTP For Forgot Password:"+str(random_otp)
    sendmail(API,from_email,to_email,subject,html_content)

    return redirect(url_for(""))

def changepassword(random_otp,newpass,otp):
    if otp==random_otp:
        sql="UPDATE REGISTER SET (PASSWORD) = (?) WHERE Inventory_ID=?" 
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,newpass)
        ibm_db.bind_param(stmt,2,session['id'])
        ibm_db.execute(stmt)
        print("password changed!")

@app.route('/updatepassword')
def updatepassword():
    random_otp=forgot()
    if request.method=='POST':
           otp=request.form['otp']
           change=request.form['newpass']
           changepassword(random_otp,change,otp)
    else:
        print("not post from forgot password")

@app.route('/sendpass')
def sendpass():
    random=forgot()
    return redirect(url_for("changed",random))'''

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/updatepassword',methods=['GET','POST'])
def updatepassword():
    msgpass=""
    if request.method=='POST':   
        mail=request.form['email']
        oldpass=request.form['oldpass'].title()
        newpass=request.form['newpass']
        print(oldpass)
        sql="SELECT COMPANY,USER_ID FROM REGISTER WHERE MAIL_ID = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,mail)
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        company=account['COMPANY']+account['USER_ID']
        oldpassdb=company
        print(oldpassdb)
        if account:
            if oldpass==oldpassdb:
                sql="UPDATE REGISTER SET (PASSWORD) = (?) WHERE MAIL_ID = ?" 
                stmt=ibm_db.prepare(conn,sql)
                ibm_db.bind_param(stmt,1,newpass)
                ibm_db.bind_param(stmt,2,mail)
                ibm_db.execute(stmt)
                print("password changed!")
                msgpass="Password Changed! Login To Continue!"
            else:
                msgpass="Old Password Does Not Match!"
        else:
            msgpass="Account Does Not Exist! Check Mail ID"
    else:
        print("not post from updatepassword")
    return render_template("Reg.html",msgpass=msgpass)

  
def count():
    sql="SELECT count(PRODUCT_ID) as PRO FROM PRODUCT WHERE INVENTORY_ID = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    account=ibm_db.fetch_assoc(stmt)
    print(account)
    session['total_pro']=account['PRO']   

    sql="SELECT count(SUPPLIER_ID) as SUP FROM SUPPLIER WHERE INVENTORY_ID = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    account=ibm_db.fetch_assoc(stmt)
    print(account)
    session['total_sup']=account['SUP']    
    
    sql="SELECT count(PRODUCT_ID) as MIN FROM PRODUCT WHERE INVENTORY_ID = ? AND AVAILABLE_PRODUCT<MIN_STOCK"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    account=ibm_db.fetch_assoc(stmt)
    print(account)
    session['total_min']=account['MIN']
    
def procount():
    list=[]
    sql="SELECT PRODUCT_GRP,SUPPLIER,COUNT(PRODUCT_ID) AS COUNT FROM PRODUCT WHERE INVENTORY_ID = ? GROUP BY PRODUCT_GRP,SUPPLIER "
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    tot_count=ibm_db.fetch_assoc(stmt)
    while tot_count != False:
        list.append(tot_count)
        tot_count = ibm_db.fetch_assoc(stmt)
    return  list

def supcount():
    list_sup=[]
    sql_sup="SELECT SUPPLIER_NAME,COUNT(PRODUCT_GRP) AS SUP_DASH FROM SUPPLIER WHERE INVENTORY_ID = ? GROUP BY SUPPLIER_NAME"
    stmt=ibm_db.prepare(conn,sql_sup)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    sup=ibm_db.fetch_assoc(stmt)
    while sup != False:
        list_sup.append(sup)
        sup = ibm_db.fetch_assoc(stmt)
    return list_sup


def checkmail(email):
    email_check=""
    if(re.fullmatch(regex_email, email)):
        email_check="Valid Email"
    else:
        email_check="Invalid Email"
    return email_check

def checkpassword(password):
    pass_check=""
    if (len(password)<6 or len(password)>12):
        pass_check="Length Of Password Should Be Between 6-12"
    elif not re.search("[a-z]",password):
        pass_check="Must Contain Lowercase Letters"
    elif not re.search("[0-9]",password):
        pass_check="Must Contain Numbers"
    elif not re.search("[A-Z]",password):
        pass_check="Must Contain Uppercase Letters"
    elif not re.search("[$#@]",password):
        pass_check="Must Contain Special Characters"
    elif re.search("\s",password):
        pass_check="Password Is Empty"
    else:
        pass_check="Valid Password"
    return pass_check

@app.route('/')
def index():
    return render_template('HomePage.html')

@app.route('/sign')
def sign():
    return render_template('Reg.html')

@app.route("/register",methods=['GET','POST'])
def register():
    error = None 
    if request.method=='POST':
           registermsg=""    
           registeraccount=""    
           company=request.form['company'].title()
           location=request.form['location'].title()
           email=request.form['email']
           username=request.form['username'].lower()
           password=request.form['password']
           mail_check=checkmail(email)
           pass_check=checkpassword(password)
           if mail_check=="Invalid Email":
                mesaagemail="Email ID Not VAlid"
                return render_template('Reg.html',mesaagemail=mesaagemail)
           elif pass_check!="Valid Password":
                mesaagemail=pass_check
                return render_template('Reg.html',mesaagemail=mesaagemail)
           else:
                sql="SELECT * FROM REGISTER WHERE MAIL_ID=?"
                prep_stmt=ibm_db.prepare(conn,sql)
                ibm_db.bind_param(prep_stmt,1,email)
                ibm_db.execute(prep_stmt)
                account=ibm_db.fetch_assoc(prep_stmt)
                print(account)
                print(company)
                if account:
                    registeraccount="Account already exists! Log in to continue !"
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
                    """subject="Registration successfull"
                    html_content="Manage Your Stock Efficiently"
                    sendmail(API,from_email,email,subject,html_content)"""
                    registermsg="Registration successfull. Log in to continue !"
                    #flash("Registration successfull. Log in to continue !")
    else:
        print("not post")
        pass
    return render_template('Reg.html',error=error,registermsg=registermsg,registeraccount=registeraccount)

@app.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        sql="SELECT * FROM REGISTER WHERE MAIL_ID=? AND PASSWORD=?"
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
            session['company_name']=account['COMPANY']
            session['company_mail']=account["MAIL_ID"]
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


@app.route('/DashBoard')
@is_logged_in
def DashBoard():
    count()
    list=procount()  
    list_sup=supcount()
    return render_template('DashBoard.html',username=session["username"],products=session['total_pro'],supplier=session['total_sup'],min=session['total_min'],listpy=list,listsup=list_sup)

@app.route('/products')
def products():
    list=[]
    #inlist=[]
    sql="SELECT PRODUCT_ID,PRODUCT_GRP,PRODUCT_NAME,TOT_QUANTITY,AVAILABLE_PRODUCT,SHIPPED,MIN_STOCK,SUPPLIER,DATE FROM PRODUCT WHERE INVENTORY_ID = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    product=ibm_db.fetch_assoc(stmt)
    print(product)
    while product != False:
        print( "The ID is : ", product["PRODUCT_ID"])
        print ("The name is : ", product["PRODUCT_GRP"])
        """inlist.append(account["PRODUCT_ID"])
        inlist.append(account["PRODUCT_GRP"])
        inlist.append(account["PRODUCT_NAME"])
        inlist.append(account["TOT_QUANTITY"])
        inlist.append(account["AVAILABLE_PRODUCT"])
        inlist.append(account["SHIPPED"])
        inlist.append(account["MIN_STOCK"])
        inlist.append(account["SUPPLIER"])
        inlist.append(account["DATE"])"""
        list.append(product)
        #inlist=[]
        product = ibm_db.fetch_assoc(stmt)
    print(list)
    return render_template('Products.html',listpy=list)

@app.route('/Supplier')
def Supplier():
    list=[]
    sql="SELECT SUPPLIER_ID,SUPPLIER_NAME,LOCATION,PH_NUMBER,Product_GRP,SupMail_ID FROM SUPPLIER WHERE INVENTORY_ID = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    supplier=ibm_db.fetch_assoc(stmt)
    print(supplier)
    while supplier != False:
        print( "The ID is : ", supplier["SUPPLIER_ID"])
        print ("The name is : ", supplier["SUPPLIER_NAME"])
        list.append(supplier)
        supplier = ibm_db.fetch_assoc(stmt)
    return render_template('Supplier.html',listpy=list)

@app.route("/search_nav",methods=['GET','POST'])
def search_nav():
    if request.method=='GET':
        search=request.args.get('search_nav')
        print(search)
        search=search.title()
        if search=="Dashboard":
            return redirect(url_for("DashBoard"))
        elif search=="Product" or search=="Products":
            return redirect(url_for("products"))
        elif search=="Supplier":
            return redirect(url_for("Supplier"))
        elif search=="Order" or search=="Orderproduct":
            return redirect(url_for("Reorder"))
        elif search=="Addproduct" or search=="Addsupplier" or search=="Operation":
            return redirect(url_for("Operation"))
        else:
            return redirect(url_for("DashBoard"))
    else:
        print("not get from search category")
        return redirect(url_for("DashBoard"))

@app.route("/search_pro",methods=['GET','POST'])
def search_pro():
    list=[]
    if request.method=='GET':
        search=request.args.get('searchpro')
        search=search.title()
        print(search)
        sql="SELECT PRODUCT_ID,PRODUCT_GRP,PRODUCT_NAME,TOT_QUANTITY,AVAILABLE_PRODUCT,SHIPPED,MIN_STOCK,SUPPLIER,DATE FROM PRODUCT WHERE INVENTORY_ID=? AND SUPPLIER=? "
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session['id'])
        ibm_db.bind_param(stmt,2,search)
        ibm_db.execute(stmt)
        product=ibm_db.fetch_assoc(stmt)
        while product != False:
            list.append(product)
            product = ibm_db.fetch_assoc(stmt)
        print(list)
    else:
        print("not get from search product")
        pass
    return render_template('Products.html',listpy=list)

@app.route("/search_sup",methods=['GET','POST'])
def search_sup():
    list=[]
    if request.method=='GET':
        search=request.args.get('searchsup')
        search=search.title()
        print(search)
        sql="SELECT SUPPLIER_ID,SUPPLIER_NAME,LOCATION,PH_NUMBER,PRODUCT_GRP,SupMail_ID FROM SUPPLIER WHERE INVENTORY_ID = ? AND LOCATION=?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session['id'])
        ibm_db.bind_param(stmt,2,search)
        ibm_db.execute(stmt)
        product=ibm_db.fetch_assoc(stmt)
        while product != False:
            list.append(product)
            product = ibm_db.fetch_assoc(stmt)
        print(list)
    else:
        print("not get from search supplier")
        pass
    return render_template('Supplier.html',listpy=list)

@app.route('/Reorder')
def Reorder():
    return render_template('Reorder.html')

@app.route('/Operation')
def Operation():
    count()
    return render_template('Operations.html',tot_sup=session['total_sup'])

@app.route('/AddProducts')
def AddProducts():
        drop_list_pro=[]
        drop_sql="SELECT Product_GRP FROM SUPPLIER WHERE Inventory_ID=?"
        stmt=ibm_db.prepare(conn,drop_sql)
        ibm_db.bind_param(stmt,1,session['id'])
        ibm_db.execute(stmt)
        drop=ibm_db.fetch_assoc(stmt)
        print(drop)
        while drop != False:
            print ("Supplier Name : ", drop["PRODUCT_GRP"])
            drop_list_pro.append(drop["PRODUCT_GRP"])
            drop = ibm_db.fetch_assoc(stmt)
        resultList_pro = list(dict.fromkeys(drop_list_pro))
        
        drop_list_sup=[]
        drop_sql="SELECT Supplier_Name FROM SUPPLIER WHERE Inventory_ID=?"
        stmt=ibm_db.prepare(conn,drop_sql)
        ibm_db.bind_param(stmt,1,session['id'])
        ibm_db.execute(stmt)
        drop=ibm_db.fetch_assoc(stmt)
        print(drop)
        while drop != False:
            print ("Supplier Name : ", drop["SUPPLIER_NAME"])
            drop_list_sup.append(drop["SUPPLIER_NAME"])
            drop = ibm_db.fetch_assoc(stmt)
        resultList_sup = list(dict.fromkeys(drop_list_sup))
        return render_template('AddProducts.html',drop_sup=resultList_sup,drop_pro=resultList_pro)

@app.route('/AddSupplier')
def AddSupplier():
    return render_template('AddSupplier.html')

@app.route("/addPro",methods=['GET','POST'])
def addPro():
    if request.method=='POST':
           pro_id=request.form['pro_id']
           pro_grp=request.form['pro_grp'].title()
           pro_name=request.form['pro_name'].title()
           Tot_Q=request.form['tot_quantity']
           Available=request.form['available']
           Shipped=request.form['Shipped']
           Minimum_stock=request.form['min_stock']
           Supplier=request.form.get('sup')
           date=request.form['date']
           sql="SELECT * FROM PRODUCT WHERE Product_ID=? AND Inventory_ID=? "
           prep_stmt=ibm_db.prepare(conn,sql)
           ibm_db.bind_param(prep_stmt,1,pro_id)
           ibm_db.bind_param(prep_stmt,2,session['id'])
           ibm_db.execute(prep_stmt)
           account=ibm_db.fetch_assoc(prep_stmt)
           print(account)
           if account:
               error="Product alread exist!"
               flash("Product alread exist!")
               return redirect(url_for("AddProducts"))
           else:
               insert_sql="INSERT INTO PRODUCT (Inventory_ID,Product_ID,Product_GRP,Product_Name,TOT_Quantity,Available_product,Shipped,Min_stock,Supplier,Date) VALUES (?,?,?,?,?,?,?,?,?,?)"
               prep_stmt=ibm_db.prepare(conn,insert_sql)
               ibm_db.bind_param(prep_stmt,1,session["id"])
               ibm_db.bind_param(prep_stmt,2,pro_id)
               ibm_db.bind_param(prep_stmt,3,pro_grp)
               ibm_db.bind_param(prep_stmt,4,pro_name)
               ibm_db.bind_param(prep_stmt,5,Tot_Q)
               ibm_db.bind_param(prep_stmt,6,Available)
               ibm_db.bind_param(prep_stmt,7,Shipped)
               ibm_db.bind_param(prep_stmt,8,Minimum_stock)
               ibm_db.bind_param(prep_stmt,9,Supplier)
               ibm_db.bind_param(prep_stmt,10,date)
               ibm_db.execute(prep_stmt)
               flash(" Product added Successfully !")
               alertmsg=alert(pro_id,pro_grp,pro_name,Tot_Q,Available,Shipped,Minimum_stock,Supplier)
               if alertmsg=="Mail Sent":
                    flash("Check Mail For Low Stock Details!")
               print("product added")
               return redirect(url_for("AddProducts"))
    else:
        pass
        return redirect(url_for("AddProducts"))

@app.route("/updatePro",methods=['GET','POST'])
def updatePro():
    error = None
    if request.method=='POST':
           pro_id=request.form['pro_id']
           pro_grp=request.form['pro_grp'].title()
           pro_name=request.form['pro_name'].title()
           Tot_Q=request.form['tot_quantity']
           Available=request.form['available']
           Shipped=request.form['Shipped']
           Minimum_stock=request.form['min_stock']
           Supplier=request.form.get('sup')
           date=request.form['date']
           update_sql="UPDATE PRODUCT SET (Product_GRP,Product_Name,TOT_Quantity,Available_product,Shipped,Min_stock,Supplier,Date) = (?,?,?,?,?,?,?,?) WHERE Inventory_ID=? AND Product_ID=? "
           prep_stmt=ibm_db.prepare(conn,update_sql)
           ibm_db.bind_param(prep_stmt,1,pro_grp)
           ibm_db.bind_param(prep_stmt,2,pro_name)
           ibm_db.bind_param(prep_stmt,3,Tot_Q)
           ibm_db.bind_param(prep_stmt,4,Available)
           ibm_db.bind_param(prep_stmt,5,Shipped)
           ibm_db.bind_param(prep_stmt,6,Minimum_stock)
           ibm_db.bind_param(prep_stmt,7,Supplier)
           ibm_db.bind_param(prep_stmt,8,date)
           ibm_db.bind_param(prep_stmt,9,session["id"])
           ibm_db.bind_param(prep_stmt,10,pro_id)
           ibm_db.execute(prep_stmt)
           print("product Updated")
           flash("Product updated Successfully !")
           alertmsg=alert(pro_id,pro_grp,pro_name,Tot_Q,Available,Shipped,Minimum_stock,Supplier)
           if alertmsg=="Mail Sent":
               flash("Check Mail For Low Stock Details!")
           return render_template('AddProducts.html',error=error)
    else:
        pass
        return render_template('AddProducts.html',error=error)

@app.route("/Edit/<string:id>/<string:grp>/<string:name>/<int:total>/<int:available>/<int:shipped>/<int:min>/<string:supplier>/<string:date>")
def Edit(id,grp,name,total,available,shipped,min,supplier,date):
    return render_template('Edit.html',id=id,grp=grp,name=name,total=total,available=available,shipped=shipped,min=min,supplier=supplier,date=date)

@app.route("/EditSup/<string:id>/<string:name>/<string:location>/<int:ph>/<string:grp>/<string:mail>")
def EditSup(id,name,location,ph,grp,mail):
    return render_template('EditSup.html',id=id,name=name,location=location,ph=ph,grp=grp,mail=mail)

@app.route("/<string:id>/<string:grp>/<string:name>/<string:supplier>/<string:date>Edit_update",methods=['GET','POST'])
def Edit_update(id,grp,name,supplier,date):
    if request.method=='POST':
           Tot_Q=request.form['tot_quantity']
           Available=request.form['available']
           Shipped=request.form['Shipped']
           Minimum_stock=request.form['min_stock']
           date=request.form['date']
           update_sql="UPDATE PRODUCT SET (TOT_Quantity,Available_product,Shipped,Min_stock,date) = (?,?,?,?,?) WHERE Inventory_ID=? AND Product_ID=? "
           prep_stmt=ibm_db.prepare(conn,update_sql)
           ibm_db.bind_param(prep_stmt,1,Tot_Q)
           ibm_db.bind_param(prep_stmt,2,Available)
           ibm_db.bind_param(prep_stmt,3,Shipped)
           ibm_db.bind_param(prep_stmt,4,Minimum_stock)
           ibm_db.bind_param(prep_stmt,5,date)
           ibm_db.bind_param(prep_stmt,6,session["id"])
           ibm_db.bind_param(prep_stmt,7,id)
           ibm_db.execute(prep_stmt)
           print("product Updated from editpage")
           flash("Product updated Successfully !")
           alertmsg=alert(id,grp,name,Tot_Q,Available,Shipped,Minimum_stock,supplier)
           if alertmsg=="Mail Sent":
                flash("Check Mail For Low Stock Details!")
           return redirect(url_for("Edit",id=id,grp=grp,name=name,total=Tot_Q,available=Available,shipped=Shipped,min=Minimum_stock,supplier=supplier,date=date))
    else:
        pass
        return redirect(url_for("Edit",id=id,grp=grp,name=name,total=Tot_Q,available=Available,shipped=Shipped,min=Minimum_stock,supplier=supplier,date=date))

@app.route("/<string:id>/<string:grp>Edit_Update_Sup",methods=['GET','POST'])
def Edit_Update_Sup(id,grp):
    error = None
    if request.method=='POST':
        sup_name=request.form['name'].title()
        location=request.form['location'].title()
        phone=request.form['phone']
        email=request.form['email']   
        update_sql="UPDATE SUPPLIER SET (Supplier_Name,Location,PH_Number,SupMail_ID) = (?,?,?,?) WHERE Inventory_ID=? AND Supplier_ID=? "
        prep_stmt=ibm_db.prepare(conn,update_sql)
        ibm_db.bind_param(prep_stmt,1,sup_name)
        ibm_db.bind_param(prep_stmt,2,location)
        ibm_db.bind_param(prep_stmt,3,phone)
        ibm_db.bind_param(prep_stmt,4,email)
        ibm_db.bind_param(prep_stmt,5,session["id"])
        ibm_db.bind_param(prep_stmt,6,id)
        ibm_db.execute(prep_stmt)
        print("Supplier Updated from editpage")
        flash("Supplier updated Successfully !")
        return redirect(url_for("EditSup",id=id,name=sup_name,location=location,ph=phone,grp=grp,mail=email))
    else:
        pass
        return redirect(url_for("EditSup",id=id,name=sup_name,location=location,ph=phone,grp=grp,mail=email))

@app.route("/EditBackSup",methods=['GET','POST'])
def EditBackSup():
    if request.method=='POST':
        return redirect(url_for("Supplier"))
    else:
        print("not get")

@app.route("/backProSup",methods=['GET','POST'])
def backProSup():
   return redirect(url_for("Operation"))

@app.route("/backPro",methods=['GET','POST'])
def backPro():
   return redirect(url_for("products"))

@app.route("/backSup",methods=['GET','POST'])
def backSup():
   return redirect(url_for("Supplier"))

@app.route("/deleteProBy/<string:id>")
def deleteProBy(id):
        print(id)
        delete_sql="DELETE FROM PRODUCT WHERE Product_ID=? AND Inventory_ID=?"
        prep_stmt=ibm_db.prepare(conn,delete_sql)
        ibm_db.bind_param(prep_stmt,1,id)
        ibm_db.bind_param(prep_stmt,2,session["id"])
        ibm_db.execute(prep_stmt)
        print("product Deleted")
        return redirect(url_for("products"))

@app.route("/deleteSupBy/<string:id>")
def deleteSupBy(id):
        print(id)
        delete_sql="DELETE FROM SUPPLIER WHERE Supplier_ID=? AND Inventory_ID=?"
        prep_stmt=ibm_db.prepare(conn,delete_sql)
        ibm_db.bind_param(prep_stmt,1,id)
        ibm_db.bind_param(prep_stmt,2,session["id"])
        ibm_db.execute(prep_stmt)
        print("Supplier Deleted")
        return redirect(url_for("Supplier"))

@app.route("/deletePro",methods=['GET','POST'])
def deletePro():
    error=None
    if request.method=='POST':
        pro_id=request.form['pro_id']
        delete_sql="DELETE FROM PRODUCT WHERE Product_ID=? AND Inventory_ID=?"
        prep_stmt=ibm_db.prepare(conn,delete_sql)
        ibm_db.bind_param(prep_stmt,1,pro_id)
        ibm_db.bind_param(prep_stmt,2,session["id"])
        ibm_db.execute(prep_stmt)
        print("product Deleted")
        flash("Product Deleted Successfully !")
        return render_template('AddProducts.html',error=error)
    else:
        pass
        return render_template('AddProducts.html',error=error)

@app.route("/addSup",methods=['GET','POST'])
def addSup():
    if request.method=='POST':
           sup_id=request.form['supID']
           sup_name=request.form['name'].title()
           location=request.form['location'].title()
           phone=request.form['phone']
           pro_grp=request.form['pro_grp'].title()
           email=request.form['email']
           mail_check=checkmail(email)
           if mail_check=="Invalid Email":
                mesaagemail="Email ID Not Valid"
                flash(mesaagemail)
                return redirect(url_for("AddSupplier"))
           sql="SELECT Supplier_ID FROM SUPPLIER WHERE SUPPLIER_ID=? AND Inventory_ID=?"
           prep_stmt=ibm_db.prepare(conn,sql)
           ibm_db.bind_param(prep_stmt,1,sup_id)
           ibm_db.bind_param(prep_stmt,2,session["id"])
           ibm_db.execute(prep_stmt)
           account=ibm_db.fetch_assoc(prep_stmt)
           print(account)
           if account:
               flash("Supplier alread exist!")
               return redirect(url_for("AddSupplier"))
           else:
               insert_sql="INSERT INTO SUPPLIER (Inventory_ID,Supplier_ID,Supplier_Name,Location,PH_Number,Product_GRP,SupMail_ID) VALUES (?,?,?,?,?,?,?)"
               prep_stmt=ibm_db.prepare(conn,insert_sql)
               ibm_db.bind_param(prep_stmt,1,session["id"])
               ibm_db.bind_param(prep_stmt,2,sup_id)
               ibm_db.bind_param(prep_stmt,3,sup_name)
               ibm_db.bind_param(prep_stmt,4,location)
               ibm_db.bind_param(prep_stmt,5,phone)
               ibm_db.bind_param(prep_stmt,6,pro_grp)
               ibm_db.bind_param(prep_stmt,7,email)
               ibm_db.execute(prep_stmt)
               print("Supplier added")
               flash("Supplier added Successfully !")
               return redirect(url_for("AddSupplier"))
    else:
        pass
        return render_template('AddSupplier.html')

@app.route("/updateSup",methods=['GET','POST'])
def updateSup():
    error = None
    if request.method=='POST':
        sup_id=request.form['supID']
        sup_name=request.form['name'].title()
        location=request.form['location'].title()
        phone=request.form['phone']
        pro_grp=request.form['pro_grp']
        email=request.form['email']   
        update_sql="UPDATE SUPPLIER SET (Supplier_Name,Location,PH_Number,Product_GRP,SupMail_ID) = (?,?,?,?,?) WHERE Inventory_ID=? AND Supplier_ID=? "
        prep_stmt=ibm_db.prepare(conn,update_sql)
        ibm_db.bind_param(prep_stmt,1,sup_name)
        ibm_db.bind_param(prep_stmt,2,location)
        ibm_db.bind_param(prep_stmt,3,phone)
        ibm_db.bind_param(prep_stmt,4,pro_grp)
        ibm_db.bind_param(prep_stmt,5,email)
        ibm_db.bind_param(prep_stmt,6,session["id"])
        ibm_db.bind_param(prep_stmt,7,sup_id)
        ibm_db.execute(prep_stmt)
        print("Supplier Updated")
        flash("Supplier updated Successfully !")
        return render_template('AddSupplier.html',error=error)
    else:
        pass
        return render_template('AddProducts.html',error=error)

@app.route("/deleteSup",methods=['GET','POST'])
def deleteSup():
    error=None
    if request.method=='POST':
        sup_id=request.form['supID']
        delete_sql="DELETE FROM SUPPLIER WHERE Supplier_ID=? AND Inventory_ID=?"
        prep_stmt=ibm_db.prepare(conn,delete_sql)
        ibm_db.bind_param(prep_stmt,1,sup_id)
        ibm_db.bind_param(prep_stmt,2,session["id"])
        ibm_db.execute(prep_stmt)
        print("Supplier Deleted")
        flash("Supplier Deleted Successfully !")
        return render_template('AddSupplier.html',error=error)
    else:
        pass
        return render_template('AddProducts.html',error=error)

@app.route("/sendordermail",methods=['GET','POST'])
def sendordermail():
    if request.method=='POST':
        print(session['company_mail'])
        #from_email=session['company_mail']
        to_email=request.form['tomail']
        subject=request.form['subject']
        html_content=request.form['text']
        print(html_content)
        sendmail(API,from_email,to_email,subject,html_content)
        print("Mail sent from sendordermail")
        mail_msg="Mail Sent!"
        return render_template('Reorder.html',ordermail=mail_msg)
    else:
        print("not post from sendordermail")
        return redirect(url_for("Reorder"))

@app.route("/sendreport")
def sendreport():
    sendreportmail()
    print("Mail sent from sendreport")
    return redirect(url_for("DashBoard"))
    

@app.route('/logout',methods=['GET','POST'])
@is_logged_in
def logout():
    #session['_flashes'].clear()
    session.clear()
    flash('You are now logged out', 'success')
    print("Logged Out")
    return redirect(url_for('index'))

if __name__=='__main__':
    app.run(debug=False,host='0.0.0.0',port=3011)