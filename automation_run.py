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


# def try_exc(fun):
#     def _te(*ages, **kwages):
#         try:
#             fun(*ages, **kwages)
#         except Exception as e:
#             print(e)
#             sleep(1)
#             fun(*ages, **kwages)
#             return
#     return _te


class Run:
    def __init__(self):
        self.data = 0
        self.cli = ClientLogin()
        
    # @try_exc
    def all_data(self):
        self.LOG_DATA = self.auto.log_data
        self.tid = self.LOG_DATA[7]
        # print(self.LOG_DATA)
        self.LOG_INFO = self.auto.res_info
        # print(self.LOG_INFO)
        self.DOWN_DATA = self.auto.down_data
        # print(self.DOWN_DATA)
    
    # 登录--clientLogin
    # @try_exc    
    def cli_run(self):
        if self.cli.run:
            return 1
        self.req_r = self.cli.req
        
    # 提交数据
    # @try_exc
    def log_run(self):
        self.log = Login(self.cli.req, self.LOG_DATA)
        self.log.run
        self.req_r = self.log.req

    # 上传xls文件
    # @try_exc
    def tra_run(self):
        self.tra = Transmission(self.cli.req, self.LOG_DATA, self.LOG_INFO)
        self.tra.run
        self.req_r = self.tra.req
		
    # @try_exc
    def dow_run(self):
        self.dow = Download(self.cli.req, self.LOG_DATA, self.DOWN_DATA)
        self.dow.run
        self.req_r = self.dow.req

    # @try_exc
    def undo_run(self):
        self.LOG_DATA = self.auto.undo_data
        self.und = Undo(self.cli.req, self.LOG_DATA)
        self.und.run
        self.req_r = self.und.req

    @property
    def run(self):
        if self.cli_run():
            return 
        os.system('taskkill /F /IM chrome.exe')
        
        while 1:
            print('in run...')
            try:
                self.auto = AutomationPipelines()
            except:
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
                print('刷新成功...等待2分钟...')
                print(strftime('%m/%d %H:%M:%S'))

                path = BASE_DIR
                try:
                    for infile in glob.glob(os.path.join(path, '*.pdf') ):  
                        os.remove(infile) 
                except:
                    print('.pdf no del')
                
                try:
                    for infile in glob.glob(os.path.join(path, '*.xls')):
                        os.remove(infile) 
                except:
                    print('.xls no del')

                sleep(120)
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
            try:
                if self.status == '111':
                    self.log_run()
            except:
                print('提交数据失败')
                
            sleep(1)
            self.status = self.auto.status(self.tid)
            try:
                if self.status == '211':
                    self.auto.data()
                    self.all_data()
                    self.tra_run()
            except Exception as e:
                print(e)
                print('xls文件上传失败')
                
            sleep(1)
            self.status = self.auto.status(self.tid)
            try:
                if self.status == '221':
                    print('归国报告书下载')
                    self.dow_run()                        
            except Exception as e:
                print(e)
                print('归国报告书下载失败')
            sleep(3)
            


if __name__ == '__main__':
    # sleep(120)
    while 1:
        print('in automation_run')
        try:
            open_client()
            while 1:
                print('in getCookies')
                if getCookies():
                    break
                sleep(10)
            r = Run()
            r.run
            
        except Exception as e:
            print('出现错误...')
            with open(BASE_DIR + '\\visa_log/error.json', 'a') as f:
                f.write(f'["{strftime("%Y-%m-%d %H:%M:%S")}", "{e}"],\n')
        finally:
            print('等待1分钟重启...')
            os.system('taskkill /f /im SecureMagicWindowsClient_1.3.1.exe')
            sleep(60)