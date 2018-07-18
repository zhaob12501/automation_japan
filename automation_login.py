import json
import os
import re

import requests

import client
from settings import *


class Login:
    def __init__(self, REQ, LOG_DATA):
        print('in Login...')
        self.req = REQ
        self.LOG_DATA = LOG_DATA
        print(self.LOG_DATA)
        # self.req.proxies = {'http': '127.0.0.1:8888', 'https': '127.0.0.1:8888'}
        # self.req.verify = False

        # 登录页面url
        self.login_url = 'https://churenkyosystem.com/member/login.php'
        # top页面url
        self.top_url = 'https://churenkyosystem.com/member/top.php'
        # top-add页面url
        self.add_url = 'https://churenkyosystem.com/member/identity_edit.php?mode=add'
        # 番号检测url
        self.agent_code_url = 'https://churenkyosystem.com/member/get_china_agent_data.php?mode=MODE_EDIT'
        # 确认信息url
        self.confirm_url = 'https://churenkyosystem.com/member/identity_edit.php?mode=add'
        if self.LOG_DATA[3] == self.LOG_DATA[9] or self.LOG_DATA[9] is None:
            self.info = '{0}（{1}）：{2}名'.format(self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[3])
        else:
            self.info = '{0}（{1}）：{2}名'.format(self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[9])

        print('in Login')

    def validation(self):
        print('in Login validation')
        res = self.req.get('https://churenkyosystem.com/member/identity_list.php')
        if self.info in res.text:
            invalid = res.text.split(self.info)[0].split('<a href="identity_info.php?IDENTITY_ID')[-1]
            if '発行済' in invalid:
                japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
                data = {'tid': self.LOG_DATA[7], 'submit_status': '211'}
                requests.post(japan_url, data=data)
                return 0
        return 1

    # 第三步 跳转至信息录入页面，并检测番号
    def top(self):
        print('in Login top')
        res = self.req.get(self.top_url)
        if res.url == self.login_url:
            print('登陆问题')
            c = client.ClientLogin()
            c.run
            self.req = c.req
            res = self.req.get(self.top_url)
            print(res.url)
        print('in Login top 2')
        res = self.req.get(self.add_url)
        assert res.url != self.login_url
        print('in Login top 3')
        reg = r'<input type="hidden" name="_PAGE_KEY" value="(.*?)" />'
        self._PAGE_KEY = re.findall(reg, res.text)[0]
        # print(self._PAGE_KEY)
        # print(res.text)

        print('in Login top data')
        # 指定番号
        data = {
            'CHINA_AGENT_CODE': self.LOG_DATA[0]
            }
        
        res = self.req.post(self.agent_code_url, data=data)
        assert res.url != self.login_url
        print(res.url)
        print(res.json())
        if res.url == self.login_url:
            c = client.ClientLogin()
            c.run
            self.req = c.req
            res = self.req.get(self.agent_code_url, data=data)
            print(res.url)
        self.res_info = res.json()
        if self.res_info == []:
            japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
            data = {'tid': self.LOG_DATA[7], 'status': '8'}
            res = requests.post(japan_url, data=data).json()
            print(res)
            return -1
        print('指定番号检索完成(指定番号の検索完了)\n番号为(番号を)：\n\t{0}\nID为(IDを)：\n\t{1}\n'
              '公司名(会社名)：\n\t{2}\n管辖公馆(管轄公館)：\n\t{3}'
              ''.format(self.res_info['COMPANY_CODE'], self.res_info['CHINA_AGENT_ID'],
                        self.res_info['COMPANY_NAME'], self.res_info['DIPLOMAT_NAME']))

    
    # 第四步 填写信息并确认
    def confirm(self):
        print('in login confirm')
        files = self.files_data()
        res = self.req.post(self.confirm_url, data=files)
        assert res.url != self.login_url
        if res.url == self.login_url:
            c = client.ClientLogin()
            c.run
            self.req = c.req
            res = self.req.get(self.confirm_url, data=files)
        reg = r'<input type="hidden" name="_PAGE_KEY" value="(.*?)" />'
        self._PAGE_KEY_2 = re.findall(reg, res.text)[0]
        # print(self._PAGE_KEY_2)

    # 第五步 提交
    def con_two(self):
        print('in Login con_two')
        data = {
            "MAIL_STATUS": "0",
            "_PAGE_KEY": self._PAGE_KEY_2,
            "BTN_CHECK_SUBMIT_x": "登 録",
        }
        try:
            res = self.req.post(self.confirm_url, data=data)
            print(res.url, res.status_code, sep='\n')
        except Exception as e:
            print(e)

        if res.url == 'https://churenkyosystem.com/member/identity_edit.php?mode=add' and res.status_code == 200:
            if self.LOG_DATA[9] is None or self.LOG_DATA[9] == self.LOG_DATA[3]:
                japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
                data = {'tid': self.LOG_DATA[7], 'submit_status': '211'}
                requests.post(japan_url, data=data).json()
                sleep(1)
            else:
                japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
                data = {'tid': self.LOG_DATA[7], 'status': '3', 'submit_status': '222'}
                requests.post(japan_url, data=data)
        
        try:
            reg = r'受付番号(.*?)<'
            self.FH = re.findall(reg, res.text)[0][1:].strip()
            print(f'\n\n===={self.FH}====\n\n')
            url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanInsertPdftext'
            data = {'tid': self.LOG_DATA[7], 'text': self.FH}
            res1 = requests.post(url, data=data).json()
            print('--', res1)
        except Exception as e:
            print(e) 
        
        print('-' * 20, '\nthe info is OK\n', '-' * 20)
        print('提交数据OK\n')
        try:
            with open(os.path.join(LOG_DIR, f'{DAY()}.json'), 'a') as f:
                log = {'提交': self.LOG_DATA, 'id': self.FH, 'time': strftime('%m/%d %H:%M:%S')}
                json.dump(log, f)
                f.write(',\n')
        except:
            pass

    # 验证数据
    def files_data(self):
        # VISA_TYPE_1 団体査証(1) 個人査証(2) 数次査証・1回目(N)
        data = {
            "CHINA_AGENT_ID": self.res_info['CHINA_AGENT_ID'],
            "CHINA_AGENT_CODE": self.res_info['COMPANY_CODE'],
            "viewAgent_company": self.res_info['COMPANY_NAME'],
            "viewAgent_diplomat": self.res_info['DIPLOMAT_NAME'],

            "APPLICANT_NAME": self.LOG_DATA[1],
            "APPLICANT_PINYIN": self.LOG_DATA[2],
            "NUMBER_OF_TOURISTS": self.LOG_DATA[3],
            "ARRIVAL_DATE":self. LOG_DATA[4],
            "DEPARTURE_DATE": self.LOG_DATA[5],

            "VISA_VISIT_TYPE": "0",
            
            "_PAGE_KEY": self._PAGE_KEY,
            "BTN_CHECK_x": "確 認"    
        }
        print('-------------------------')
        info = {
        '单次签证': 1,
        '冲绳单次签证': 1,
        '团体查证': 2,
        '冲绳三年签证': 3,
        '东北六县三年（青森）': 4,
        '东北六县三年（岩手）': 5,
        '东北六县三年（宫城）': 6,
        '东三县1三年宫城签证': 6,
        '东北六县三年（秋田）': 7,
        '东北六县三年（山形）': 8,
        '东北六县三年（福岛）': 9,
        '三年多次签证': 10,
        }

        add_info = info[self.LOG_DATA[6]]
        print(add_info)
        if add_info is 1:
            data["VISA_TYPE"] = '2'
            data["VISA_TYPE_1"] = '2'
            data["VISA_TYPE_2"] = '4'
        elif add_info is 2:
            data["VISA_TYPE"] = '1'
            data["VISA_TYPE_1"] = '1'
        elif add_info is 3:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_47"] = '47'
        elif add_info is 4:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_2"] = '2'
        elif add_info is 5:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_3"] = '3'
        elif add_info is 6:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_4"] = '4'
        elif add_info is 7:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_4"] = '5'
        elif add_info is 8:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_6"] = '6'
        elif add_info is 9:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_7"] = '7'
        elif add_info is 10:
            data["VISA_TYPE"] = '4'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '4'

        print(data)
        return data
    
    @property
    def run(self):
        try:
            if self.validation():
                self.top()

                sleep(2)

                self.confirm()

                sleep(2)

                self.con_two() 
                print('=========')
            return 1
        except Exception as e:
            print('automation_login 出现错误...')
            with open(BASE_DIR + '\\visa_log/error.json', 'a') as f:
                f.write(f'["automation_login", "{strftime("%Y-%m-%d %H:%M:%S")}", "{e}"],\n')
            sleep(3)
            japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
            data = {'tid': self.LOG_DATA[7], 'status': '2'}
            res = requests.post(japan_url, data=data).json()
            print(res)
            assert 'login error' == '' 
         

if __name__ == '__main__':
    pass
