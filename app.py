import os
from flask import (Flask, request)
import face_recognition as fc


app = Flask(__name__)
print("__name__ is", __name__)

UPLOAD_FOLDER = '/uploads'

face_encodings = []
rolando1 = fc.load_image_file("./uploads/rolando1.jpeg")
rolando1_encoding = fc.face_encodings(rolando1, None, 1)[0]

mario1 = fc.load_image_file("./uploads/mario1.jpg")
mario1_encoding = fc.face_encodings(mario1)[0]
mario2 = fc.load_image_file("./uploads/mario2.jpeg")
mario2_encoding = fc.face_encodings(mario2)[0]
face_encodings.append(rolando1_encoding)
face_encodings.append(mario1_encoding)
face_encodings.append(mario2_encoding)

names = ["Rolando", "Mario", "Mario"]

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        print(file)
        extension = os.path.splitext(file.filename)[1]
        name_to_save = "unknown_latest_image" + extension
        #name_to_save = file.filename
        file.save(os.path.join("./uploads/", name_to_save))
    
    return findFace(name_to_save)

def findFace(name_to_save):
    print(name_to_save)
    unknown_image = fc.load_image_file("./uploads/"+name_to_save)
    unknown_image_encoding = fc.face_encodings(unknown_image)
    if (len(unknown_image_encoding)==0):
        print("couldn't find face")
        return "No Face"
    print("Size: ", len(unknown_image_encoding))
    results = fc.compare_faces(face_encodings, unknown_image_encoding[0], tolerance=0.6)
    index = 0
    for result in results:
        if result==True:
            return names[index]
        index+=1
    return "Unknown"


if __name__ == '__main__':
    #app.run(host="13.68.140.235", port="5007")
    app.run(host='0.0.0.0', debug=True, threaded=True)

