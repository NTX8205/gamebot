import json
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("firebasekey.json") #設置自己的firebase存取金鑰
firebase_admin.initialize_app(cred)
db = firestore.client()
sched = BlockingScheduler()


@sched.scheduled_job("interval", days=1)
def timed_job():
	url = "https://api.gamebase.com.tw/api/news/getNewsList"
	type=["pc","mobile","handheld"]
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
			news = data['return_msg']['list']
			for list in news:
				newsnum = "No."+list['news_no']
				doc = {
					"title": list["news_title"],
					"picture": list["news_img"],
					"hyperlink": "https://news.gamebase.com.tw/news/detail/"+list['news_no'],
					"showDate": list["post_time"],
					"showtype": list["system"]
				}
				doc_ref = db.collection(i).document(newsnum)
				doc_ref.set(doc)



sched.start()