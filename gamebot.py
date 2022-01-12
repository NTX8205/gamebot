from datetime import datetime, timezone, timedelta
import json
import requests
from flask import Flask, render_template, request, make_response, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("firebasekey.json") #設置自己的firebase存取金鑰
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/getnews")
def news():
    tz = timezone(timedelta(hours=+8))
    now = datetime.now(tz)
    url = "https://api.gamebase.com.tw/api/news/getNewsList"
    type = ["pc", "mobile", "handheld"]
    for i in type:
        payload = {
            'category': i,
            'page': 1,
            'GB_type': "newsList"
            }
        headers = {
            'content-type': "application/json",
            }
        r = requests.post(url=url, data=json.dumps(payload), headers=headers)
        if r.status_code == requests.codes.ok:
            data = r.json()
            news = data["return_msg"]["list"]
            for list in news:
                newsnum = "No."+list["news_no"]
                doc = {
					"title": list["news_title"],
					"picture": list["news_img"],
					"hyperlink": "https://news.gamebase.com.tw/news/detail/"+list['news_no'],
					"showDate": list["post_time"],
					"showtype": list["system"]
				}
                doc_ref = db.collection(i).document(newsnum)
                doc_ref.set(doc)
    return "資料已全數上傳 上傳日期:"+str(now)

@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action = req.get("queryResult").get("action")   
    if(action=="gamingnews"):
        type = req.get("queryResult").get("parameters").get("game")
        if(type=="pc"):
            typename="PC"
        elif(type == "mobile"):
            typename="手機遊戲"
        elif(type == "handheld"):
            typename = "TV掌機"
        info="查詢的新聞類型 : "+typename+"\n\n"
        
        collection_ref = db.collection(type)
        docs = collection_ref.order_by("showDate", direction=firestore.Query.DESCENDING).limit(5).get()
        for doc in docs:
            info += "新聞標題：" + doc.to_dict()["title"] + "\n" 
            info += "新聞連結：" + doc.to_dict()["hyperlink"] + "\n"
            info += "新聞類型：" + doc.to_dict()["showtype"] + " \n" 
            info += "日期：" + doc.to_dict()["showDate"] + "\n\n"
        text=info
    return make_response(jsonify({"fulfillmentText": info}))    

if __name__ == "__main__":
    app.run()
