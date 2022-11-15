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
    return render_template('Reg.html',msg=" ")
    
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
    
    list=[]  
    sql="SELECT PRODUCT_GRP,SUPPLIER,COUNT(PRODUCT_ID) AS COUNT FROM PRODUCT WHERE INVENTORY_ID = ? GROUP BY PRODUCT_GRP,SUPPLIER "
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    tot_count=ibm_db.fetch_assoc(stmt)
    while tot_count != False:
        list.append(tot_count)
        tot_count = ibm_db.fetch_assoc(stmt)

    list_sup=[]
    sql_sup="SELECT SUPPLIER_NAME,COUNT(PRODUCT_GRP) AS SUP_DASH FROM SUPPLIER WHERE INVENTORY_ID = ? GROUP BY SUPPLIER_NAME"
    stmt=ibm_db.prepare(conn,sql_sup)
    ibm_db.bind_param(stmt,1,session['id'])
    ibm_db.execute(stmt)
    sup=ibm_db.fetch_assoc(stmt)
    while sup != False:
        list_sup.append(sup)
        sup = ibm_db.fetch_assoc(stmt)

    return render_template('Dashboard.html',username=session["username"],products=session['total_pro'],supplier=session['total_sup'],min=session['total_min'],listpy=list,listsup=list_sup)

@app.route('/products')
@is_logged_in
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
@is_logged_in
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


@app.route("/search_pro",methods=['GET','POST'])
@is_logged_in
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
        print("not post y")
        pass
    return render_template('Products.html',listpy=list)

@app.route("/search_sup",methods=['GET','POST'])
@is_logged_in
def search_sup():
    list=[]
    if request.method=='GET':
        search=request.args.get('searchsup')
        search=search.title()
        print(search)
        sql="SELECT SUPPLIER_ID,SUPPLIER_NAME,LOCATION,PH_NUMBER,PRODUCT_GRP,SupMail_ID FROM SUPPLIER WHERE INVENTORY_ID = ? AND SUPPLIER_NAME=? or PRODUCT_GRP=? OR LOCATION=?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session['id'])
        ibm_db.bind_param(stmt,2,search)
        ibm_db.bind_param(stmt,3,search)
        ibm_db.bind_param(stmt,4,search)
        ibm_db.execute(stmt)
        product=ibm_db.fetch_assoc(stmt)
        while product != False:
            list.append(product)
            product = ibm_db.fetch_assoc(stmt)
        print(list)
    else:
        print("not post y")
        pass
    return render_template('Supplier.html',listpy=list)

@app.route('/Operation')
@is_logged_in
def Operation():
    return render_template('Operations.html',tot_sup=session['total_sup'])

@app.route('/AddProducts')
@is_logged_in
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
@is_logged_in
def AddSupplier():
    return render_template('AddSupplier.html')

@app.route("/addPro",methods=['GET','POST'])
@is_logged_in
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
               print("product added")
               flash(" Product added Successfully !")
               return redirect(url_for("AddProducts"))
    else:
        pass
        return redirect(url_for("AddProducts"))

@app.route("/updatePro",methods=['GET','POST'])
@is_logged_in
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
   return redirect(url_for("Operation"))

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


@app.route('/logout')
@is_logged_in
def logout():
    #session['_flashes'].clear()
    session.clear()
    flash('You are now logged out', 'success')
    print("Logged Out")
    return redirect(url_for('login'))

if __name__=='__main__':
    app.run(debug=True)