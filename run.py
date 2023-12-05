from flask import Flask, render_template,request,session,redirect,url_for
from flask_socketio import SocketIO,leave_room, join_room,send
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

rooms = {}
def gen_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code+=random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code
@app.route("/",methods=["GET","POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        create = request.form.get("create",False)
        join = request.form.get("join",False)
        if not name:
            return render_template("home.html",error="Please input a name",code=code,name=name)
        if join !=False and not code:
            return render_template("home.html",error="Please put a code.",code=code,name=name)
        room = code
        if create != False:
            room = gen_unique_code(4)
            rooms[room] = {"members":0,"messages":[]}
        elif code not in rooms:
            return render_template("home.html",error="this room doesn't exist")
        session["room"]=room
        session["name"]=name
        return redirect(url_for("room"))
    return render_template("home.html")
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html",room=room,messages=rooms[room]["messages"])

#sockets
@socketio.on("connect")
def connect():
    name = session.get("name")
    room = session.get("room")
    if not room or not name:
        return 
    if room not in rooms:
        leave_room(room)
        return 
    join_room(room)
    send({"name":name,"message":"has entered the room"},to=room)
    rooms[room]["members"]+=1
    print(f'{name} joined room {room}')
    print(rooms[room]["members"])

@socketio.on("disconnect")
def disconnect():
    name = session.get("name")
    room = session.get("room")
    if room in rooms:
        rooms[room]["members"]-=1
        if rooms[room]["members"]<=0:
            del rooms[room]
    send({"name":name,"message":"has left the room"},to=room)
    print(f'{name} has left room {room}')

@socketio.on("message")
def handle_msgs(data):
    room = session.get("room")
    if room not in rooms:
        return
    content ={"name":session.get("name"),
              "message":data["data"]}
    send(content,to=room)
    rooms[room]["messages"].append(content)
    print(f'{session.get("name")} said:{data["data"]}')
    return render_template("room.html",)

if __name__ == '__main__':
    app.run(debug=True)
    socketio.run(app)
