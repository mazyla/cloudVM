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
def sqlQuery():
    if request.method == 'GET':
        print("Query to run: ", request.args['query'])
        cursor.execute(request.args['query']) # run query, send to SQL server
        row = cursor.fetchone() # get first line of result
        iphone_response = {} # so that we can have a json format
        i = 0
        while row:
             print(row)
             iphone_response[i] = str(row) # each result has its own key, consecutively
             row = cursor.fetchone()
             i += 1
        return json.dumps(iphone_response)


if __name__ == '__main__':
    # app.run(host="13.68.140.235", port="5007")
    app.run(host='0.0.0.0', debug=True, threaded=True)
