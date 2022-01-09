from linebot.models import (MessageEvent, TextMessage,
                            TextSendMessage, ImageSendMessage, LocationSendMessage)
from linebot.exceptions import (InvalidSignatureError)
from linebot import (LineBotApi, WebhookHandler)
from bs4 import BeautifulSoup
import json
import requests
import subprocess
from flask import Flask, render_template, request, abort, make_response, jsonify
from datetime import datetime, timezone, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("firebasekey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
line_bot_api = LineBotApi(
    jdata['token'])
handler = WebhookHandler(jdata['channel'])

with open('setting.json', 'r', encoding='utf8') as jfile:
    jdata = json.load(jfile)

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
