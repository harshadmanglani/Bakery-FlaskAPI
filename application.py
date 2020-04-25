# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import flask 
import json
import sqlite3
import random 
import string 
from flask import Flask, request, render_template


# %%
class DBops:

    def __init__(self, dbname):
        self.dbname = dbname

    def initdb(self):
        self.conn = sqlite3.connect(self.dbname)
        self.c = self.conn.cursor()
        return [self.c, self.conn]
    
    def search(self, Email, Password):
        var = self.initdb()
        c = var[0]
        conn = var[1]
        c.execute('''SELECT*FROM Users WHERE Email = ? AND Password = ?''', (Email, Password))
        data = c.fetchone()
        conn.close()
        return data 

    def invalidateaccesstoken(self, accesstoken):
        var = self.initdb()
        c = var[0]
        conn = var[1]
        print("Accesstoken in invalidate:", accesstoken)
        c.execute('''DELETE FROM AccessTokens WHERE AccessToken = ?''', (accesstoken, ))
        conn.commit()
        c.execute("SELECT*FROM AccessTokens WHERE AccessToken = ?", (accesstoken, ))
        data = c.fetchall()
        print("Is token deleted: ", data)
        conn.close()
        return True

    def generateaccesstokenandstore(self, uid):
        var = self.initdb()
        c = var[0]
        conn = var[1]
        accesstoken = None
        c.execute('''SELECT*FROM AccessTokens WHERE UID = ?''', (uid, ))
        var = c.fetchone()
        if  var == None:
            isLoggedIn = False 
        else:
            print("Accesstoken found:", var)
            isLoggedIn = True
        print("Logged in: ", isLoggedIn) 
        if isLoggedIn is False:
            accesstoken = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 8))
            c.execute('''INSERT INTO AccessTokens (UID, AccessToken) VALUES(?,?)''', (uid, accesstoken))
            conn.commit()
        print("Accesstoken in generate:", accesstoken)
        conn.close()
        return accesstoken

    def registernewuser(self, email, password):
        var = self.initdb()
        c = var[0]
        conn = var[1]
        c.execute('''INSERT INTO Users (Email, Password) VALUES (?, ?)''', (email , password))
        conn.commit()
        conn.close()

    def displaystores(self, accesstoken):
        var = self.initdb()
        c = var[0]
        conn = var[1]
        if self.isvalidtoken(accesstoken):
            print("valid token")
            c.execute('''SELECT*FROM Stores''')
            data = c.fetchall()
            conn.close()
            return data
        else:
            print("token invalid")
            conn.close()
            return None
        

    def isvalidtoken(self, accesstoken):
        var = self.initdb()
        c = var[0]
        conn = var[1]
        c.execute('SELECT*FROM AccessTokens WHERE AccessToken = ?',(accesstoken, ))
        data = c.fetchone()
        print("Is accesstoken validddd:", data)
        if data is None:
            conn.close()
            return False 
        else:
            conn.close()
            return True


# %%
db = DBops('APITest.sqlite')
app = Flask(__name__)

@app.route('/', methods = ["GET", "POST"])
def initFunc():
    return "Hello Azure!"
    
@app.route('/login', methods = ["GET", "POST"])
def loginFunc():
    try:
        parameters = request.get_json(force = True)
        email = parameters["email"]
        password = parameters["password"]
        data = db.search(email, password)
        print("Data", data)
        if data is None:
            return json.dumps({"login": False, "accesstoken" : None})
        uid = data[0]
        accesstoken = db.generateaccesstokenandstore(uid)
        print("accesstoken in loginFunc:", accesstoken)
        return json.dumps({"login": True, "accesstoken": accesstoken})
    except:
        return json.dumps({"login": False, "accesstoken" : None, "error": True})    

@app.route('/logout', methods = ["GET", "POST"])
def logoutFunc():
    try:
        parameters = request.get_json(force = True)
        accesstoken = parameters["accesstoken"]
        var = db.invalidateaccesstoken(accesstoken)
        if var:
            return json.dumps({"logout" : True})
        else:
            return json.dumps({"logout" : False})
    except:
        return json.dumps({"logout" : False, "error": True})

@app.route('/register', methods = ["GET", "POST"])
def registerFunc():
    try:
        parameters = request.get_json(force = True)
        email = parameters["email"]
        password = parameters["password"]
        db.insert(email, password)
        data = db.search(email, password)
        if data is None:
            return json.dumps({"login": False, "accesstoken" : None})
        uid = data[0]
        accesstoken = db.generateaccesstokenandstore(uid)
        return json.dumps({"login": True, "accesstoken": accesstoken})
    except:
        return json.dumps({"login": False, "accesstoken" : None, "error": True}) 

@app.route('/stores', methods = ["GET", "POST"])
def displaystoresFunc():
    try:
        parameters = request.get_json(force = True)
        accesstoken = parameters["accesstoken"]
        data = db.displaystores(accesstoken)
        print("stores: ", data)
        if data is None:
            return {"stores": None}
        print(data)
        storeslist = []
        for i in data: 
            jsondata = {"name": i[1], "flavours": json.loads(i[2])}
            storeslist.append(jsondata)
        
        return json.dumps({"stores": storeslist})
    except:
        return json.dumps({"stores": None, "error" : True})


# %%
if __name__ == "__main__":
    app.run(debug = False)

