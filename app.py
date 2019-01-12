from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO, emit
import random
import time


min_number, max_number = 0, 100
users = {}
message = ""

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app)

def gen_num():
  return random.randint(1, 99)

number = gen_num()
print(number)

@app.route('/')
@app.route("/home")
def index():
  return render_template("index.html")

@app.route("/end-game")
def end_game():
  return render_template("end_game.html")

@socketio.on("users_list")
def userslist(username):
  nick = username
  if nick not in users.values():
    if not users:
      users.update({1 : nick})
    else:
      users.update({len(users) + 1 : nick})
  else:
    emit("nick_error", {"url" : url_for("index")}, broadcast=False)

@socketio.on("post")
def post(data):
  username = data["username"]
  message = data["msg"]

  reply = int(message)

  global number
  global min_number
  global max_number

  if reply < number and (reply >= min_number):
    min_number = reply
  elif reply > number and (reply <= max_number):
    max_number = reply

  if reply == number:
    message = "Reply: {} - {} LOSED!".format(reply, username)
  elif number + 1 == max_number and number - 1 == min_number:
    for id_, user in users.items():
      if username == user:
        if id_ + 1 > max(users, key=int):
          message = "Reply: {} - {} HAS BEEN SQUASHED!".format(reply, users[1])
          break
        else:
          message = "Reply: {} - {} HAS BEEN SQUASHED!".format(reply, users[id_ + 1])
          break
  elif reply < number and (reply > min_number or reply == min_number):
    message = "Reply: {} - The number is between {} and {}".format(reply, reply, max_number)
  elif reply < min_number or reply > max_number:
    message = "Reply: {} - The number is between {} and {}".format(reply, min_number, max_number)
  elif reply > number and (reply < max_number or reply == max_number):
    message = "Reply: {} - The number is between {} and {}".format(reply, min_number, reply)

  if len(users) > 1:
    if not message.__contains__("LOSED") and not message.__contains__("HAS"):
      for user_id, nick in users.items():
        if username == nick:
          if user_id + 1 > max(users, key=int):
            message = "{} - Your turn, {}".format(message, users[1])
            break
          else:
            message = "{} - Your turn, {}".format(message, users[user_id + 1])
            break
  else:
    message = "{} - Wait for opponent...".format(message)

  emit("client_side", {"username" : username, "message" : message}, broadcast=True)
  
  if message.__contains__("LOSED") or message.__contains__("HAS"):
    print("Generating a new number...")
    gen_num()
    number = gen_num()
    print(number)
    users.clear()
    time.sleep(5)
    emit("redirect", {"url" : url_for("end_game")}, broadcast=True)

@socketio.on("quit")
def quit(user):
  player_id = dict((v,k) for k,v in users.items()).get(user)
  users.pop(player_id, None)
  emit("user_disconnected", users[player_id], broadcast=True)

if __name__ == "__main__":
  socketio.run(app, debug=True, host="192.168.100.107", port=9999)


