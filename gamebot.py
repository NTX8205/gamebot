from linebot.models import (MessageEvent, TextMessage,TextSendMessage, ImageSendMessage, LocationSendMessage)
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

@app.route('/spider')
def spider():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    lastUpdate = sp.find("div", class_="smaller09").text[5:]

    for item in result:
        picture = item.find("img").get("src").replace(" ", "")
        title = item.find("div", class_="filmtitle").text
        movie_id = item.find("div", class_="filmtitle").find(
            "a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw" + \
            item.find("div", class_="filmtitle").find("a").get("href")
        show = item.find("div", class_="runtime").text.replace("上映日期：", "")
        show = show.replace("片長：", "")
        show = show.replace("分", "")
        showDate = show[0:10]
        showLength = show[13:]

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "lastUpdate": lastUpdate
        }

        doc_ref = db.collection("電影").document(movie_id)
        doc_ref.set(doc)
    return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate


@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]
        collection_ref = db.collection("電影")
        docs = collection_ref.order_by("showDate").get()
        info = ""
        for doc in docs:
            if MovieTitle in doc.to_dict()["title"]:
                info += "片名：" + doc.to_dict()["title"] + "<br>"
                info += "海報：" + doc.to_dict()["picture"] + "<br>"
                info += "影片介紹：" + doc.to_dict()["hyperlink"] + "<br>"
                info += "片長：" + doc.to_dict()["showLength"] + " 分鐘<br>"
                info += "上映日期：" + doc.to_dict()["showDate"] + "<br><br>"
        return info
    else:
        return render_template("input.html")


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    if(message[:5].upper() == 'MOVIE'):
        res = searchMovie(message[6:])
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=res))
    elif(message.upper() == "TCYANG"):
        line_bot_api.reply_message(event.reply_token, ImageSendMessage(
            original_content_url="https://www1.pu.edu.tw/~tcyang/aboutme/family.jpg",
            preview_image_url="https://www1.pu.edu.tw/~tcyang/aboutme/family.jpg"
        ))
    elif(message.upper() == "PU"):
        line_bot_api.reply_message(event.reply_token, LocationSendMessage(
            title="靜宜大學地理位置",
            address="台中市沙鹿區臺灣大道七段200號",
            latitude=24.22649,
            longitude=120.5780923
        ))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我是電影機器人，您輸入的是：" + message + "。祝福您有個美好的一天！"))


def searchMovie(keyword):
    info = "您要查詢電影，關鍵字為：" + keyword + "\n"
    collection_ref = db.collection("電影")
    docs = collection_ref.order_by("showDate").get()
    found = False
    for doc in docs:
        if keyword in doc.to_dict()["title"]:
            found = True
            info += "片名：" + doc.to_dict()["title"] + "\n"
            info += "海報：" + doc.to_dict()["picture"] + "\n"
            info += "影片介紹：" + doc.to_dict()["hyperlink"] + "\n"
            info += "片長：" + doc.to_dict()["showLength"] + " 分鐘\n"
            info += "上映日期：" + doc.to_dict()["showDate"] + "\n\n"

    if not found:
       info += "很抱歉，目前無符合這個關鍵字的相關電影喔"
    return info


@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action = req.get("queryResult").get("action")
    #msg =  req.get("queryResult").get("queryText")
    #info = "動作：" + action + "； 查詢內容：" + msg
    if (action == "CityWeather"):
        city = req.get("queryResult").get("parameters").get("city")
        info = "查詢都市名稱：" + city + "，天氣："
        city = city.replace("台", "臺")
        token = "CWB-3529EB57-A2A7-4A64-A265-20174D01C663"
        url = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=" + \
            token + "&format=JSON&locationName=" + str(city)
        Data = requests.get(url)
        Weather = json.loads(Data.text)[
            "records"]["location"][0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        Rain = json.loads(Data.text)[
            "records"]["location"][0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
        info += Weather + "，降雨機率：" + Rain + "%"
    elif (action == "searchMovie"):
        cond = req.get("queryResult").get("parameters").get("FilmQ")
        keyword = req.get("queryResult").get("parameters").get("any")
        info = "您要查詢電影的" + cond + "，關鍵字是：" + keyword + "\n\n"

        if (cond == "片名"):
            collection_ref = db.collection("電影")
            docs = collection_ref.order_by("showDate").get()
            found = False
            for doc in docs:
                if keyword in doc.to_dict()["title"]:
                    found = True
                    info += "片名：" + doc.to_dict()["title"] + "\n"
                    info += "海報：" + doc.to_dict()["picture"] + "\n"
                    info += "影片介紹：" + doc.to_dict()["hyperlink"] + "\n"
                    info += "片長：" + doc.to_dict()["showLength"] + " 分鐘\n"
                    info += "上映日期：" + doc.to_dict()["showDate"] + "\n\n"
            if not found:
                info += "很抱歉，目前無符合這個關鍵字的相關電影喔"
    return make_response(
        jsonify({
            "fulfillmentText": info,
            "fulfillmentMessages": [
                {"quickReplies": {
                    "title": info,
                    "quickReplies": ["台北天氣", "台中天氣", "高雄天氣"]
                }}]
        }))

if __name__ == "__main__":
    app.run()
