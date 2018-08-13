import glob
import os

import requests

from automation_download import Download
from automation_login import Login
from automation_transmission import Transmission
from automation_undo import Undo
from client import ClientLogin, getCookies, open_client
from pipelines import AutomationPipelines
from settings import *


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
        self.tra = Transmission(self.cli.req, self.LOG_DATA, self.LOG_INFO, self.auto)
        self.tra.run
        self.req_r = self.tra.req
		
    def dow_run(self):
        self.dow = Download(self.cli.req, self.LOG_DATA, self.DOWN_DATA, self.auto)
        self.dow.run
        self.req_r = self.dow.req

    def undo_run(self):
        print(self.LOG_DATA)
        self.und = Undo(self.cli.req, self.LOG_DATA, self.auto)
        self.und.run
        self.req_r = self.und.req

    @property
    def run(self):
        # ==========
        # 登陆exe程序
        # ==========
        if self.cli_run():
            return 
        os.system('taskkill /F /IM chrome.exe')
        pool = POOL() 
        # ========
        # 开始执行
        # ========
        while True:
            print('\nin run...')
            try:
                self.auto = AutomationPipelines(pool)
            except:
                if self.auto:
                    del self.auto
                print('数据库连接超时...重连...')
                continue
            print('数据库连接完毕...')

            self.data = self.auto.data()
            if not self.data:
                print('没有数据, 准备刷新...')
                if self.cli.refresh(self.req_r):
                    print('刷新失败...退出...')
                    break
                if self.auto:
                    del self.auto 
                print('刷新成功...等待...')
                print(strftime('%m/%d %H:%M:%S'))

                path = BASE_DIR
                try:
                    for infile in glob.glob(os.path.join(path, '*.pdf') ):  
                        os.remove(infile) 
                except:
                    print('.pdf no del')

                sleep(5)
                continue

            # =======
            # 数据处理
            # =======
                   
            # 判断是否需要申请
            print('\n有数据进行提交\n')

            # 获取需要申请的人员信息
            self.all_data()
            
            self.control[self.status]()

            if self.auto:
                del self.auto 
            if self.tid:
                del self.tid


if __name__ == '__main__':
    # sleep(120)

    while True:
        print('in automation_run')
        try:
            open_client()
            while True:
                print('in getCookies')
                if getCookies():
                    break
                sleep(10)
            r = Run()
            r.run
            
        except Exception as e:
            print('automation_run 出现错误...')
            ERRINFO(r.err, None, "automation_run", e)
        finally:
            print('系统重启...')
            os.system('taskkill /f /im SecureMagicWindowsClient_1.3.1.exe')
            os.system('taskkill /f /im chrome.exe')