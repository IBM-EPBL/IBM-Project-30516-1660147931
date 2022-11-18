from  flask import Flask,render_template,url_for,request,flash,session,redirect
import ibm_db
import re
from functools import wraps
from tabulate import tabulate


app=Flask(__name__)
app.secret_key='ay'
try:
    conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=ba99a9e6-d59e-4883-8fc0-d6a8c9f7a08f.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=31321;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=hkl72011;PWD=EWU0l3XLa6KfY4Kf","","")
except:
    print("Unable to connect: ",ibm_db.conn_error())

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
    '''+tabulate(list_pro,tablefmt='fancy_grid')+'''
    Supplier Details:
    '''+tabulate(list_sup, tablefmt='fancy_grid')+'''

    Regards,
    IStock'''
    html_content=content_first+content_second
    sendmail(API,from_email,to_email,subject,html_content)


  
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
    return render_template('Dashboard.html',username=session["username"],products=session['total_pro'],supplier=session['total_sup'],min=session['total_min'],listpy=list,listsup=list_sup)

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
    return redirect(url_for('login'))

if __name__=='__main__':
    app.run(debug=True)