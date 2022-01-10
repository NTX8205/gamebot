from linebot.models import (MessageEvent, TextMessage,
                            TextSendMessage, ImageSendMessage, LocationSendMessage)
from linebot.exceptions import (InvalidSignatureError)
from linebot import (LineBotApi, WebhookHandler)
from bs4 import BeautifulSoup
import json
import requests
from flask import Flask, render_template, request, abort, make_response, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("firebasekey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
with open('key.json', 'r', encoding='utf8') as jfile:
    jdata = json.load(jfile)
line_bot_api = LineBotApi(jdata["token"])
handler = WebhookHandler(jdata["channel"])


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action = req.get("queryResult").get("action")
    if(action == "gamingnews"):
        info = ""
        type = req.get("queryResult").get("parameters").get("game")
        url = "https://api.gamebase.com.tw/api/news/getNewsList"

        payload = {
            'category': type,
            'page': 1,
            'GB_type': "newsList"
        }
        headers = {
            'content-type': "application/json",
        }
        r = requests.post(url=url, data=json.dumps(payload), headers=headers)

        if r.status_code == requests.codes.ok:
            data = r.json()
            news = data['return_msg']['list']
            for news1 in news[:20]:
                str = "https://news.gamebase.com.tw/news/detail/" + \
                    news1['news_no']
                info += str+"\n"+news1['news_title']+"\n"
        else:
            print('請求失敗')

    return make_response(jsonify({"fulfillmentText": info}))


if __name__ == "__main__":
    app.run()
