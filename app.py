import os
from flask import (Flask, request)
import face_recognition as fc
import json
import pyodbc

# Azure SQL parameters to set up connection
# found in Azure Portal
server = 'smartlockmqpserver.database.windows.net'
database = 'smartLockSQL'
username = 'mazyla'
password = 'Team1centaur2'
# Install driver: https://www.microsoft.com/en-us/sql-server/developer-get-started/python/ubuntu/
driver= '{ODBC Driver 17 for SQL Server}'

cnxn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()


app = Flask(__name__)
print("__name__ is", __name__)

UPLOAD_FOLDER = '/uploads' # where it is storing images (temporary)

face_encodings = [] # holds a list of known face encodings
# Load from local storage and encode a face
rolando1 = fc.load_image_file("./uploads/rolando1.jpeg")
rolando1_encoding = fc.face_encodings(rolando1, None, 1)[0] 

mario1 = fc.load_image_file("./uploads/mario1.jpg")
mario1_encoding = fc.face_encodings(mario1)[0]
mario2 = fc.load_image_file("./uploads/mario2.jpeg")
mario2_encoding = fc.face_encodings(mario2)[0]

# append all known faces to known face encodings
face_encodings.append(rolando1_encoding)
face_encodings.append(mario1_encoding)
face_encodings.append(mario2_encoding)

names = ["Rolando", "Mario", "Mario"] # same index as when added to face encodings

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# Handle uploading an image
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        print(file)
        extension = os.path.splitext(file.filename)[1]
        name_to_save = "unknown_latest_image" + extension
        # name_to_save = file.filename
        file.save(os.path.join("./uploads/", name_to_save))

    return findFace(name_to_save)

# Tries to find a face by comparing
# unknown_latest_image.jpg to known face encodings
def findFace(name_to_save):
    print(name_to_save)
    unknown_image = fc.load_image_file("./uploads/" + name_to_save)
    unknown_image_encoding = fc.face_encodings(unknown_image)
    if (len(unknown_image_encoding) == 0):
        print("couldn't find face")
        return "No Face"
    print("Size: ", len(unknown_image_encoding))
    # check face encodings to see if we recognize the unknown face
    # results is a list of bool: true if face found on the same index as 
    # appears in face_encodings
    results = fc.compare_faces(face_encodings, unknown_image_encoding[0], tolerance=0.6)
    index = 0
    for result in results:
        if result == True:
            return names[index]
        index += 1
    return "Unknown"

# Handle GET SQL queries
@app.route('/sqlQuery', methods=['GET', 'POST'])
# Get request from iphone
# request object needs to be handled different;y for GET and POST
def getIphoneRequest():
    # Get a user from the database
    if request.method == 'GET':
        queryResults = buildQuery( request.args )
        return queryResults

    
    # TO BE ORGANIZED
    #if request.method == 'GET':
        #print("Query to run: ", request.args['infoRequested'])
        # different requests coming from iPhone
        #queryResults = buildQuery("allUsersInfo", None)
        #return queryResults
    if request.method == 'POST':
        queryResults = buildQuery( request.get_json() )
        return queryResults
        
        #print("Key of json", request.get_json().get('users'))
        #if request.get_json().get('addUsers') != None:
        #    #get all users in post request
        #    users = request.get_json().get('addUsers')
        #    print("Users ", users)
            # users is a dictionary with many users with id as key and 
            # another dictionary as values. The values dictionary has 
            # db fields as keys and its values as values "first": "Aleksander"
            #for userID in users.keys():
                #print("userID ", userID)
        #    queryResult = buildQuery("addUsers", users)
        #    return queryResult
        #print("iPhone is trying to store: ", request.get_json())
        
        #print("Dictionary of users: ", toStore)


def buildQuery( iphoneRequest ):
    # Attributes for Users and Friends
    userKeys = ['id','firstName','lastName','email', 'password']
    friendsKeys = ['id','firstName','lastName','comeInDays','doorNotification']

    infoRequested = iphoneRequest.get('infoRequested')
    
    # Get all the users from DB
    if infoRequested == "allUsersInfo":
        query = "SELECT * FROM App_User;"
    
    if infoRequested == "addUsers":
        dataToAdd = iphoneRequest.get("addUsers")
        for userId, user in dataToAdd.items():
            # Get proper query to add user  
            firstName = user.get("first")
            lastName = user.get("last")
            email = user.get("email")
            query = "INSERT INTO App_User VALUES (%d,'%s','%s','%s')" % ( int(userId), firstName, lastName, email )
            cursor.execute(query)
            cnxn.commit()            
        return 'SUCCESS' 
    
    # Gets a user from the database if found
    if infoRequested == "getUserAuthentication":
        email = iphoneRequest.get("email")
        password = iphoneRequest.get("password")

        # Get users
        query = "SELECT * FROM UserInfo WHERE UserEmail = '%s' AND UserPassword = '%s' " % ( email, password ) 
        cursor.execute(query)
        row = cursor.fetchone()
        
        if row == None:
            return json.dumps( {'Failure': '0'} )
        userList = [ x for x in row ]  
        userDic = myList2Dic( userKeys, userList )  
        # Get friends 
        query2 = "SELECT F.* FROM UserInfo U, Friend F WHERE U.UserId = %d AND U.UserId = F.UserId" % ( userList[0] ) 
        cursor.execute(query2)
        
        # parse all friends
        friendsDic = {}
        row = cursor.fetchone()
        while row:
            friendList = [ x for x in row ]
            # Get dictionary from friend without foreign key
            friendsDic[ friendList[0] ] = myList2Dic( friendsKeys, friendList[:-1] )
            row = cursor.fetchone()
        
        userDic['friends'] = friendsDic 

        return json.dumps( userDic )

    
    else:
        cursor.execute("SELECT * FROM App_User")
        row = cursor.fetchone()  # get first line of result
        iphone_response = {}  # so that we can have a json format

        while row:  # for as long as we have data in the table in db
            print("Row:", row)
            rowList = [ x for x in row ]  # list of data for a single row
            print("rowlist: ", rowList )
            uID = rowList[0]
            iphone_response[ uID ] = rowList  # userID: [user data]
            row = cursor.fetchone()
        
        return json.dumps(iphone_response)

# Returns a dictionary with the given keys and values 
def myList2Dic( keys , myList ):
    myDic = {}
    for idx, val in enumerate(myList):
        myDic[ keys[idx] ] = myList[ idx ]

    return myDic

if __name__ == '__main__':
    # app.run(host="13.68.140.235", port="5007")
    app.run(host='0.0.0.0', debug=True, threaded=True)
