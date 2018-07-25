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
        
    def all_data(self):
        self.LOG_DATA = self.auto.log_data
        self.tid = self.LOG_DATA[7]
        # print(self.LOG_DATA)
        self.LOG_INFO = self.auto.res_info
        # print(self.LOG_INFO)
        self.DOWN_DATA = self.auto.down_data
        # print(self.DOWN_DATA)
    
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
        log_data = self.auto.undo_data
        print(log_data)
        self.und = Undo(self.cli.req, log_data, self.auto)
        self.und.run
        self.req_r = self.und.req

    @property
    def run(self):
        if self.cli_run():
            return 
        os.system('taskkill /F /IM chrome.exe')
        
        while True:
            print('in run...')
            try:
                self.auto = AutomationPipelines()
                self.auto.get_travel_name()
            except:
                try:
                    del self.auto
                except:
                    pass
                print('数据库连接超时...20秒后重连...')
                sleep(20)
                continue
            print('数据库连接完毕...')
            if self.auto.get_res:
                print('没有数据, 准备刷新...')
                if self.cli.refresh(self.req_r):
                    print('刷新失败...退出...')
                    break
                del self.auto
                try:
                    del self.tid
                except:
                    pass
                print('刷新成功...等待半分钟...')
                print(strftime('%m/%d %H:%M:%S'))

                path = BASE_DIR
                try:
                    for infile in glob.glob(os.path.join(path, '*.pdf') ):  
                        os.remove(infile) 
                except:
                    print('.pdf no del')

                sleep(30)
                continue

            up = self.auto.undo_p()
            # 判断是否需要撤销
            print('是否需要撤销:(1/0): ', up)
            if up:              
                self.undo_run()
                sleep(1)
                continue
            else:
                self.data = self.auto.data()
                sleep(1)
            
            # 判断是否需要申请
            print('是否需要申请:(1/0): ', self.data)

            # 获取需要申请的人员信息
            self.all_data()
            self.status = self.auto.status(self.tid)
            if self.status == '111':
                self.log_run()
                
            sleep(1)
            if self.status == '211':
                self.tra_run()
                
            sleep(1)
            if self.status == '221':
                print('归国报告书下载')
                self.dow_run()                        
            sleep(1)

            del self.auto 


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
            with open(BASE_DIR + '\\visa_log/error.json', 'a') as f:
                f.write(f'["automation_run", "{strftime("%Y-%m-%d %H:%M:%S")}", "{e}"],\n')
        finally:
            print('等待1分钟重启...')
            os.system('taskkill /f /im SecureMagicWindowsClient_1.3.1.exe')
            os.system('taskkill /f /im chrome.exe')
            sleep(60)
