import os
import logging
from logging.handlers import TimedRotatingFileHandler

from flask import Flask
from flask_restful import Api

from resources.line import Callback


app = Flask(__name__)

app.logger.setLevel(logging.INFO)

# 建立一個 TimedRotatingFileHandler 物件，設定日誌檔案的名稱及最低處理的日誌級別
# 'midnight' 表示每天凌晨創建新的日誌檔案，backupCount 是指定保留多少份日志
file_handler = TimedRotatingFileHandler("./logs/app.log", when="midnight", backupCount=7)
file_handler.setLevel(logging.INFO)

# 建立一個 Formatter 物件，設定日誌訊息的格式
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

# 將 Formatter 物件加入到 FileHandler 物件中
file_handler.setFormatter(formatter)

# 將 FileHandler 物件加入到 logger 中
app.logger.addHandler(file_handler)

api = Api(app)

api.add_resource(Callback, "/callback")
