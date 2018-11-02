import json
import os
import random
import re

import requests

import client
from settings import sleep, strftime, DAY, AutomationError, LOG_DIR, ERRINFO


class Undo:
    def __init__(self, req, LOG_DATA, auto=""):
        print('启动撤回模块...')
        self.auPipe = auto
        self.req = req
        self.FH = LOG_DATA[8]

        self.LOG_DATA = LOG_DATA
        self.identity_list_url = 'https://churenkyosystem.com/member/identity_list.php'
        self.identity_name_url = 'https://churenkyosystem.com/member/identity_name_list.php?IDENTITY_ID={}'
        self.i_nup_e_url = 'https://churenkyosystem.com/member/identity_nameupload_edit.php?IDENTITY_ID={}'

        if self.LOG_DATA[3] == self.LOG_DATA[9] or self.LOG_DATA[9] is None:
            self.info = '{0}（{1}）：{2}名'.format(
                self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[3])
        else:
            self.info = '{0}（{1}）：{2}名'.format(
                self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[9])
        # 登录页面url
        self.login_url = 'https://churenkyosystem.com/member/login.php'

        self.run

    # 1、 进入搜索信息搜索列表，并搜索指定ID
    def search_info(self):
        print('进入搜索信息搜索列表，并搜索指定ID')
        print(self.FH)
        if self.FH:
            print('检索信息-有番号查询')
            data = {
                'CODE': self.FH,
                'PAGE_VIEW_NUMBER': '0',
                'BTN_SEARCH_x': '検 索',
            }

            res = self.req.post(self.identity_list_url, data=data)
            reg = r'<a href="identity_info\.php\?IDENTITY_ID=(.*?)">{}</a>'.format(
                self.FH)
            self.identity_id = re.findall(reg, res.text)
            print(f'检索成功, id: {self.identity_id}!执行撤回操作!')
        else:
            # 1、 进入搜索信息搜索列表，并搜索指定ID
            print('检索信息-无番号查询')
            try:
                res = self.req.get(self.identity_list_url)
                if res.url == self.login_url:
                    raise AutomationError('登陆失效, 重新登陆...')
                self.identity_id = res.text.split(self.info, 1)[1].split(
                    '<tr class="', 1)[1].split('"', 1)[0][-7:]
                print(f'检索成功, id: {self.identity_id}!执行撤回操作!')

            except:
                try:
                    for i in range(1, 31):
                        ne = f'?p={i}&s=1&d=2'
                        url = self.identity_list_url + ne
                        res = self.req.get(url)
                        if res.url == self.login_url:
                            raise AutomationError('登陆失效...')
                        try:
                            self.identity_id = res.text.split(self.info, 1)[1].split(
                                '<tr class="', 1)[1].split('"', 1)[0][-7:]
                            print(f'检索成功, id: {self.identity_id}!执行撤回操作!')
                            self.get_url = url
                            break
                        except:
                            continue
                    else:
                        self.auPipe.update(tid=self.LOG_DATA[7], submit_status='111')
                        return 
                except:
                    self.auPipe.update(tid=self.LOG_DATA[7], submit_status='111')
        if not self.identity_id:
            self.auPipe.update(self.LOG_DATA[7], submit_status="111", pdf="")
        self.identity_id = self.identity_id[0]
            

    # 2、执行撤销操作
    def undo(self):
        data = {
            'IDENTITY_ID': self.identity_id,
            'CANCEL_TYPE': random.choice(['2', '3'])
        }
        res = self.req.post(
            'https://churenkyosystem.com/member/set_cancel_identity.php', data=data)
        if res.url == self.login_url:
            raise AutomationError('登陆失效, 重新登录...')
        sleep(3)

        self.auPipe.update(tid=self.LOG_DATA[7], submit_status='111')
        print('==========\n撤回请求成功!\n==========')

        with open(os.path.join(LOG_DIR, f'{DAY()}.json'), 'a') as f:
            log = {'撤销': self.LOG_DATA,
                   'id': self.LOG_DATA[-1], 'time': strftime('%m/%d %H:%M:%S')}
            json.dump(log, f)
            f.write(',\n')

        res = self.req.get('https://churenkyosystem.com/member/top.php')
        if res.url == self.login_url:
            raise AutomationError('登陆失效...')

    @property
    def run(self):
        sleep(1)
        try:
            self.search_info()
            sleep(1)
            self.undo()
        except AttributeError as ate:
            self.auPipe.update(tid=self.LOG_DATA[7], status='2')
            raise AutomationError(ate, "automation_undo")
        except IndexError:
            self.auPipe.update(tid=self.LOG_DATA[7], status='2')
            raise AutomationError("列表超出范围", "automation_undo")
        except AutomationError:
            raise AutomationError('登陆失效, 重新登陆...', "automation_undo")
        except Exception as e:
            print('automation_undo 出现错误...')
            ERRINFO(self.LOG_DATA[7], self.LOG_DATA[1], "automation_undo", e)
            raise AutomationError(e, "automation_undo")
        finally:
            del self.auPipe
