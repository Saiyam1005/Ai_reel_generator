from flask import Flask, render_template,request
import uuid,os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'user_upload'
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def home():
    reel_folder = "static/reel"
    reels = [f for f in os.listdir(reel_folder) if f.endswith(".mp4")]
    return render_template("index.html", reels=reels)
    # return render_template("index.html",reels=reels)

@app.route("/create",methods=["GET", "POST"])
def create():
    myid = uuid.uuid1()
    if request.method == "POST":
        print("Files uploaded:", request.files.keys())
        rec_id = request.form.get("uuid")
        desc = request.form.get("text")
        input_files = []
        for key,value in request.files.items():
            print(key,value)
            file = request.files[key]
            if file:
                filename = secure_filename(file.filename)
                if (not (os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'],rec_id)))):
                    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'],rec_id))
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],rec_id, filename))
                input_files.append(file.filename)

            with open(os.path.join(app.config['UPLOAD_FOLDER'],rec_id,"description.txt"),"w") as f:
                f.write(desc)
        for fl in input_files:
            with open(os.path.join(app.config['UPLOAD_FOLDER'],rec_id, "input.txt"),"a") as f:
                f.write(f"file '{fl}'\n duration 1\n")
        # with open(os.path.join(app.config['UPLOAD_FOLDER'],rec_id, "input.txt"), "w") as f:
        #     for fl in input_files:
                # f.write(f"file '{fl}'\n")
    return render_template("create.html",myid=myid)

@app.route("/gallery")
def gallery():
    reels = os.listdir("static/reel")
    return render_template("gallery.html",reels=reels)

app.run(debug=True)