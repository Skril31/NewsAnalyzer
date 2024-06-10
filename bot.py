import asyncio
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot
from telegram.constants import ParseMode
from peewee import *

db = SqliteDatabase('news.db')
db.connect()


class BaseModel(Model):
    class Meta:
        database = db
        table_name = "news"


class News(BaseModel):
    id = PrimaryKeyField()
    title = TextField()
    url = TextField()
    content = TextField()
    annotation = TextField()
    name_entity = TextField()
    flag_annotation = IntegerField()
    flag_news = IntegerField()


bot = None
updateIntervalSeconds = 10
TOKEN = ''
CHAT_ID = '518992122'
bot = Bot(TOKEN)
# if len(sys.argv) > 2:
#     TOKEN = '7241784770:AAE27EVG_BHjtbmFCubv7uUW0SepW1nSP20'
#     CHAT_ID = '518992122'
#     bot = Bot(TOKEN)
#     if len(sys.argv) > 3:
#         updateIntervalSeconds = sys.argv[3]
# else:
#     print("Usage: bot.py token channel_id [update_interval_seconds: default = 10]")
#     sys.exit()


async def run():
    news = News.select().where(
        (News.flag_news.is_null() | News.flag_news == 0)
        & (News.flag_annotation == 1)
    )
    for n in news:
        tags = ' '.join(list(map(lambda tag: f'#{tag.replace(" ", "_")}', n.name_entity.split(', '))))
        charsToEscape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        replace = ['\\' + l for l in charsToEscape]
        trans = str.maketrans(dict(zip(charsToEscape, replace)))
        message = f"""
*{n.title.translate(trans)}*
{n.url.translate(trans)}

_{n.annotation.translate(trans)}_

{tags.translate(trans)}
"""
        await bot.sendMessage(CHAT_ID,
                              message,
                              parse_mode=ParseMode.MARKDOWN_V2,
                              disable_web_page_preview=True)
        n.flag_news = 1
        n.save()


def _schedule():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run, trigger=IntervalTrigger(seconds=updateIntervalSeconds))
    scheduler.start()
    print('Press Ctrl+C to exit')

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    _schedule()


