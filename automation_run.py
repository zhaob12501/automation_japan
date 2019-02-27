import glob
import os
import re

import requests

from automation_download import Download
from automation_login import Login
from automation_transmission import Transmission
from automation_undo import Undo
from client import ClientLogin, getCookies, open_client
from pipelines import AutomationPipelines
from settings import BASE_DIR, ERRINFO, TIM, AutomationError, sleep, strftime

reboot = 3


class SendEmail:
    def __init__(self, req, LOG_DATA):
        self.req = req
        self.LOG_DATA = LOG_DATA
        self.identity_list_url = 'https://churenkyosystem.com/member/identity_list.php'
        self.id_r_e_url = 'https://churenkyosystem.com/member/identity_return_edit.php?IDENTITY_ID={}'

    # 1、 进入搜索信息搜索列表，并搜索指定ID
    def search_info(self):
        # print('进入搜索信息搜索列表，并搜索指定ID:', self.LOG_DATA[8])
        if self.LOG_DATA[8]:
            # print('检索信息-有番号查询')
            data = {
                'CODE': self.LOG_DATA[8],
                'PAGE_VIEW_NUMBER': '0',
                'BTN_SEARCH_x': '検 索',
            }

            res = self.req.post(self.identity_list_url, data=data)
            reg = r'<a href="identity_info\.php\?IDENTITY_ID=(.*?)">{}</a>'.format(
                self.LOG_DATA[8])
            self.identity_id = re.findall(reg, res.text)[0]
            # print('The Download first step to success!')
            # print(self.identity_id)
        else:
            return 1

    def send_email(self):
        res = self.req.get(self.id_r_e_url.format(str(self.identity_id) + "&action=republish"))
        reg = r'<input type="hidden" value="(.*?)" name="_PAGE_KEY">'
        _PAGE_KEY = re.findall(reg, res.text)[0]
        data = {
            "_PAGE_KEY": _PAGE_KEY,
            "action": "republish",
            "BTN_REPUBLISH_x": "再発行",
        }
        self.req.post(self.id_r_e_url.format(self.identity_id), data=data)


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
        self.req = self.cli.req

    # 提交数据
    def log_run(self):
        # print(self.LOG_DATA)
        self.log = Login(self.req, self.LOG_DATA, self.auto)
        self.log.run
        self.req = self.log.req

    # 上传xls文件
    def tra_run(self):
        self.tra = Transmission(self.req, self.LOG_DATA,
                                self.LOG_INFO, self.auto)
        self.tra.run
        self.req = self.tra.req

    def dow_run(self):
        self.dow = Download(self.req, self.LOG_DATA, self.auto)
        self.dow.run
        self.req = self.dow.req

    def undo_run(self):
        # print(self.LOG_DATA)
        self.und = Undo(self.req, self.LOG_DATA, self.auto)
        self.und.run
        self.req = self.und.req

    @property
    def run(self):
        global reboot
        if self.cli_run():
            return -1

        # 开始执行
        while True:
            # print('\nin Run...')
            url = "http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/sqlWhere"
            data = {
                "name": "travel_business_list",
                "where": "status=1 or status=2 or submit_status=3"
            }
            res = requests.post(url, data=data, timeout=5)
            if res.json():
                self.auto = AutomationPipelines()
                if not self.auto.data():
                    break
                # 数据处理
                # print('\n有数据进行提交\n')

                # 获取需要申请的人员信息
                self.all_data()
                self.control[self.status]()
            else:
                self.auto = None
                # print('没有数据, 等待...', strftime('%m/%d %H:%M:%S'))
                if self.cli.refresh(self.req):
                    break
                reboot = 3
                for infile in glob.glob(os.path.join(BASE_DIR, '*.pdf')):
                    os.remove(infile)

                sleep(5)


def client():
    os.system('taskkill /F /IM SecureMagicWindowsClient_1.3.1.exe')
    # 登陆exe程序
    open_client()
    os.system('taskkill /F /IM chrome.exe')


if __name__ == '__main__':
    client()
    while True:
        try:
            # print('in automation_run')
            r = Run()
            if r.run == -1:
                client()
        except Exception:
            reboot -= 1
            if not reboot:
                client()
            # print('automation_run 出现错误... 系统重启...')
            ERRINFO(name="系统重启", file="automation_run")
