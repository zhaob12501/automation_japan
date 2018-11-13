import glob
import os

import requests

from automation_download import Download
from automation_login import Login
from automation_transmission import Transmission
from automation_undo import Undo
from client import ClientLogin, getCookies, open_client
from pipelines import AutomationPipelines
from settings import POOL, sleep, strftime, BASE_DIR, ERRINFO, AutomationError, TIM


class Run:
    def __init__(self, req):
        self.req = req
        self.data = 0
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

    # 提交数据
    def log_run(self):
        print(self.LOG_DATA)
        self.log = Login(self.req, self.LOG_DATA, self.auto)
        self.log.run
        self.req = self.log.req

    # 上传xls文件
    def tra_run(self):
        self.tra = Transmission(self.req, self.LOG_DATA, self.LOG_INFO, self.auto)
        self.tra.run
        self.req = self.tra.req

    def dow_run(self):
        self.dow = Download(self.req, self.LOG_DATA, self.auto)
        self.dow.run
        self.req = self.dow.req

    def undo_run(self):
        print(self.LOG_DATA)
        self.und = Undo(self.req, self.LOG_DATA, self.auto)
        self.und.run
        self.req = self.und.req

    def run(self, con):
        self.auto = AutomationPipelines(con)
        self.auto.data()

        # 获取需要申请的人员信息
        self.all_data()
        self.control[self.status]()


def main():
    cli = ClientLogin()
    if cli.run:
        return
    req = cli.req
    os.system('taskkill /F /IM chrome.exe')

    # 开始执行
    while True:
        url = "http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/sqlWhere"
        data = {
            "name": "travel_business_list",
            "where": "status=1 or status=2 or submit_status=3"
        }
        res = requests.post(url, data=data)
        if res.json():
            r = Run(req)
            con = pool.connection()
            r.run(con)
            req = r.req
        else:
            r = None
            print('没有数据, 准备刷新...')
            if cli.refresh(req):
                print('刷新失败...退出...')
                break
            print('刷新成功...等待...')
            print(strftime('%m/%d %H:%M:%S'))

            path = BASE_DIR
            try:
                for infile in glob.glob(os.path.join(path, '*.pdf')):
                    os.remove(infile)
            except:
                print('.pdf no del')

            sleep(5)
            continue

if __name__ == '__main__':
    pool = POOL()
    while True:
        try:
            print('in automation_run')
            # 登陆exe程序f
            open_client()

            print('in getCookies')
            for i in range(10):
                if getCookies():
                    break
            else:
                continue

            # 主程序
            main()
        except Exception:
            print('automation_run 出现错误... 系统重启...')
            ERRINFO(name="系统重启", file="automation_run")
        finally:
            os.system('taskkill /f /im SecureMagicWindowsClient_1.3.1.exe')
            os.system('taskkill /f /im chrome.exe')
