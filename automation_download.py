import json
import re
import os

import requests

import client
from settings import sleep, strftime, AutomationError, LOG_DIR, ERRINFO, DAY, INTERFACE


class Download:
    def __init__(self, req, LOG_DATA, auto=""):
        self.auPipe = auto
        self.req = req
        self.LOG_DATA = LOG_DATA
        self.SLFH = self.LOG_DATA[8][:9] + ".pdf"

        if self.LOG_DATA[3] == self.LOG_DATA[9] or self.LOG_DATA[9] is None:
            self.info = '{0}（{1}）：{2}名'.format(
                self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[3])
        else:
            self.info = '{0}（{1}）：{2}名'.format(
                self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[9])
        # 登录页面url
        self.login_url = 'https://churenkyosystem.com/member/login.php'
        self.identity_list_url = 'https://churenkyosystem.com/member/identity_list.php'
        self.id_r_e_url = 'https://churenkyosystem.com/member/identity_return_edit.php?IDENTITY_ID={}'

    # 1、 进入搜索信息搜索列表，并搜索指定ID
    def search_info(self):
        # print('进入搜索信息搜索列表，并搜索指定ID')
        # print(self.LOG_DATA[8])
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
            # 1、 进入搜索信息搜索列表，并搜索指定ID
            # print('检索信息-无番号查询')
            try:
                res = self.req.get(self.identity_list_url)
                if res.url == self.login_url:
                    raise AutomationError('登陆失效...')
                self.identity_id = res.text.split(self.info, 1)[1].split(
                    '<tr class="', 1)[1].split('"', 1)[0][-7:]
                # print('The Download first step to success!')
                # print(self.identity_id)

            except Exception:
                for i in range(1, 21):
                    ne = '?p={}&s=1&d=2'.format(i)
                    url = self.identity_list_url + ne
                    res = self.req.get(url)
                    if res.url == self.login_url:
                        raise AutomationError('登陆失效...')
                    try:
                        self.identity_id = res.text.split(self.info, 1)[1].split(
                            '<tr class="', 1)[1].split('"', 1)[0][-7:]
                        # print('The Download first step to success!')
                        self.get_url = url
                        break
                    except Exception:
                        continue
                # else:
                    # print('Your records are too old. Please resubmit your information!...')

    def identity_return(self):
        url = self.id_r_e_url.format(self.identity_id)

        res = self.req.get(url)
        if res.url == self.login_url:
            raise AutomationError('登陆失效...')

        # print('The Download second step is successful')
        reg = '<input type="hidden" value="(.*?)"  name="_PAGE_KEY" />'
        self._PAGE_KEY = re.findall(reg, res.text)[0]

        data = {
            "JAPAN_PREPARED": "",
            "CHINA_TEL": "",
            "CHINA_FAX": "",
            "CHINA_PREPARED": "",
            "GROUP_NAME": "",
            "NUMBER_OF_TOURISTS_MALE": "",
            "NUMBER_OF_TOURISTS_FEMALE": "",
            "TOURISTS_ADDRESS": "",
            "NUMBER_OF_ESCORT": "",
            "NUMBER_OF_GUIDE": "",
            "CHANGE_SCHEDULE_CONTENTS": "",
            "CHANGE_SCHEDULE_REASON": "",
            "TRANSLATOR_NAME": "",
            "TRANSLATOR_PREF": "",
            "TRANSLATOR_NUMBER": "",
            "TRANSLATOR_CONTACT": "",
            "JAPAN_ESCORT_NAME": "",
            "JAPAN_ESCORT_CONTACT": "",
            "JAPAN_ESCORT_DEPARTMENT": "",
            "CHINA_ESCORT_NAME": "",
            "CHINA_ESCORT_CONTACT": "",
            "CHINA_ESCORT_DEPARTMENT": "",
            "PASSENGER_NAME": "",
            "PASSENGER_ADDRESS": "",
            "PASSENGER_TEL": "",
            "PASSENGER_NUMBER": "",
            "PASSENGER_AREA": "",
            "FLIGHT_NUMBER": "",
            "DEPARTURE_PLACE": "",
            "DEPARTURE_TIME": "",
            "ARRIVAL_PLACE": "",
            "ARRIVAL_TIME": "",
            "_PAGE_KEY": self._PAGE_KEY,
            "BTN_CHECK_x": '確認'
        }

        res = self.req.post(url, data=data)
        if res.url == self.login_url:
            raise AutomationError('登陆失效...')
        reg = r'<input type="hidden" value="(.*?)"  name="_PAGE_KEY" />'
        self._PAGE_KEY = re.findall(reg, res.text)[0]
        # print('The Download third step is successful')

        data = {
            "_PAGE_KEY": self._PAGE_KEY,
            "BTN_CHECK_SUBMIT_x": '登 録'
        }
        res = self.req.post(url, data=data)
        if res.url == self.login_url:
            c = client.ClientLogin()
            c.run
            self.req = c.req
            res = self.req.get(url)

        # reg = r"window\.open\('\.(.*?)', '_blank'\);"

        self.down_url = res.text.split(
            "window.open('.")[1].split("', '_blank');")[0]
        # print('Download the fourth step is successful')

    def down(self):
        url = 'https://churenkyosystem.com/member' + self.down_url
        url = url + self.identity_id if url[-1] == "=" else url
        res = self.req.get(url)
        if res.url == self.login_url:
            raise AutomationError('登陆失效...')
        file = {"file": res.content}

        data = {'tid': f'{self.LOG_DATA[7]}'}
        res = requests.post(INTERFACE, data=data, files=file)
        if res.json()['status'] == 1:
            self.auPipe.update(tid=self.LOG_DATA[7], status='3', submit_status='222')

            # print('-' * 20, '\nthe info is OK\n', '-' * 20)
            with open(os.path.join(LOG_DIR, f'{DAY()}.json'), 'a') as f:
                log = {'归国': "", 'time': strftime('%m/%d %H:%M:%S')}
                json.dump(log, f)
                f.write(',\n')
            # print('归国报告书下载OK\n')
        else:
            self.auPipe.update(tid=self.LOG_DATA[7], status='2')

    @property
    def run(self):
        try:
            self.search_info()
            sleep(1)
            self.identity_return()
            sleep(1)
            self.down()
        except AttributeError as ate:
            self.auPipe.update(tid=self.LOG_DATA[7], status='2')
            raise AutomationError(ate, "automation_download")
        except IndexError:
            self.auPipe.update(tid=self.LOG_DATA[7], status='2')
            raise AutomationError("列表超出范围", "automation_download")
        except AutomationError:
            raise AutomationError('登陆失效, 重新登陆...', "automation_download")
        except Exception as e:
            # print('automation_download 出现错误...')
            ERRINFO(self.LOG_DATA[7], self.LOG_DATA[1],
                    "automation_download", e)
            raise AutomationError(e, "automation_download")
        sleep(1)
