import glob
import os

import requests

from automation_download import Download
from automation_login import Login
from automation_transmission import Transmission
from automation_undo import Undo
from client import ClientLogin, getCookies, open_client
from pipelines import AutomationPipelines
from settings import sleep, strftime, BASE_DIR, ERRINFO, AutomationError, TIM


class Run:
    def __init__(self):
        self.data = 0
        self.cli = ClientLogin()
        self.control = {
            '3': self.undo_run,
            '111': self.log_run,
            '211': self.tra_run,
            '221': self.dow_run
        }

    def all_data(self):
        self.LOG_DATA = self.auto.log_data
        self.tid = self.LOG_DATA[7]
        self.status = self.LOG_DATA[10]
        self.LOG_INFO = self.auto.res_info
        self.DOWN_DATA = self.auto.down_data

    # 登录--clientLogin
    def cli_run(self):
        if self.cli.run:
            return 1
        self.req_r = self.cli.req

    # 提交数据
    def log_run(self):
        print(self.LOG_DATA)
        self.log = Login(self.cli.req, self.LOG_DATA, self.auto)
        self.log.run
        self.req_r = self.log.req

    # 上传xls文件
    def tra_run(self):
        self.tra = Transmission(
            self.cli.req, self.LOG_DATA, self.LOG_INFO, self.auto)
        self.tra.run
        self.req_r = self.tra.req

    def dow_run(self):
        self.dow = Download(self.cli.req, self.LOG_DATA, self.auto)
                            # self.DOWN_DATA, 
        self.dow.run
        self.req_r = self.dow.req

    def undo_run(self):
        print(self.LOG_DATA)
        self.und = Undo(self.cli.req, self.LOG_DATA, self.auto)
        self.und.run
        self.req_r = self.und.req

    @property
    def run(self):
        if self.cli_run():
            return
        os.system('taskkill /F /IM chrome.exe')
        # 开始执行
        while True:
            print('\nin Run...')
            url = "http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/sqlWhere"
            data = {
                "name": "travel_business_list",
                "where": "status=1 or status=2 or submit_status=3"
            }
            res = requests.post(url, data=data)
            if res.json():
                self.auto = AutomationPipelines()
                self.auto.data()
                # 数据处理

                # 判断是否需要申请
                print('\n有数据进行提交\n')

                # 获取需要申请的人员信息
                self.all_data()
                self.control[self.status]()

            else:
                print('没有数据, 等待...')
                if self.cli.refresh(self.req_r):
                    break
                print(strftime('%m/%d %H:%M:%S'))

                for infile in glob.glob(os.path.join(BASE_DIR, '*.pdf')):
                    os.remove(infile)

                sleep(5)


if __name__ == '__main__':
    while True:
        try:
            print('in automation_run')
            # 登陆exe程序
            open_client()
            for _ in range(10):
                print('in getCookies')
                if getCookies():
                    break
                sleep(10)
            else:
                continue

            r = Run()
            r.run
        except Exception:
            print('automation_run 出现错误... 系统重启...')
            ERRINFO(name="系统重启", file="automation_run")
        finally:
            os.system('taskkill /f /im SecureMagicWindowsClient_1.3.1.exe')
            os.system('taskkill /f /im chrome.exe')
