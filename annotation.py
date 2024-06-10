import requests
import time
import sqlite3
import json
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models.gigachat import GigaChat

def create_annotations(texts):
    url = "https://api.aicloud.sbercloud.ru/public/v2/summarizator/predict"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    for text in texts:
        try:
            text=text[0]
            request = {
                "instances": [
                    {
                        "text": text,
                        "num_beams": 3,
                        "num_return_sequences": 6,
                        "length_penalty": 1.5,
                        "repetition_penalty": 1.5,
                        "genstrategy": "beamsearch"
                    }
                ]
            }
            res = requests.post(url=url,headers=headers,json=request)
            print(res.status_code)
            annotation = json.loads(res.text)
            if(res.status_code==200 and annotation["comment"]=="Ok!"):
                annotation = annotation["prediction_best"]["bertscore"]
                with sqlite3.connect("news.db") as con:
                    cursor = con.cursor()
                    flag=1
                    cursor.execute("UPDATE news SET annotation = ?, flag_annotation = ? WHERE content = ?", (annotation, flag, text))
                    con.commit()
            else:
                with sqlite3.connect("news.db") as con:
                    cursor = con.cursor()
                    flag=1
                    cursor.execute("UPDATE news SET annotation = ?, flag_annotation = ? WHERE content = ?", ("-", flag, text))
                    con.commit()

            time.sleep(1)
        except Exception as e:
            print(f"Ошибка при получении доступа к api: {e}")
            with sqlite3.connect("news.db") as con:
                cursor = con.cursor()
                flag = 1
                cursor.execute("UPDATE news SET annotation = ?, flag_annotation = ? WHERE content = ?",
                               ("-", flag, text))
                con.commit()

def create_neural_annotations(texts):
    chat = GigaChat(
        credentials='ZGIyOTY3ZGItZDJjMS00MTI1LWIwY2ItODY1YzgzNDdhMjI0OmM3MDIxMzgxLWFmMzUtNGM1My1iODk1LTZkYTU5YzAyZjgzOQ==',
        verify_ssl_certs=False)
    messages = [
        SystemMessage(
            content="Ты бот который должен создавать краткие аннотации к новостям."
        )
    ]
    for text in texts:
        try:
            text = text[0]
            messages.append(HumanMessage(content=text))
            res = chat(messages)
            messages.append(res)
            annotation = res.content

            with sqlite3.connect("news.db") as con:
                cursor = con.cursor()
                flag=1
                cursor.execute("UPDATE news SET annotation = ?, flag_annotation = ? WHERE content = ?", (annotation, flag, text))
                con.commit()
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка при получении доступа к api: {e}")
            with sqlite3.connect("news.db") as con:
                cursor = con.cursor()
                flag = 1
                cursor.execute("UPDATE news SET annotation = ?, flag_annotation = ? WHERE content = ?",
                               ("-", flag, text))
                con.commit()