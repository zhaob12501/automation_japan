import json
import os
import re

import requests

import client
from settings import DAY, sleep, strftime, AutomationError, LOG_DIR, ERRINFO


class Login:
    def __init__(self, REQ, LOG_DATA, auto=""):
        print('in Login...')
        self.req = REQ
        self.LOG_DATA = LOG_DATA

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
            self.info = '{0}（{1}）：{2}名'.format(
                self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[3])
        else:
            self.info = '{0}（{1}）：{2}名'.format(
                self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[9])

        self.auPipe = auto

    # def validation(self):
        # print('in Login validation')
        # res = self.req.get(
        #     'https://churenkyosystem.com/member/identity_list.php')
        # if self.info in res.text:
        #     invalid = res.text.split(self.info)[0].split(
        #         '<a href="identity_info.php?IDENTITY_ID')[-1]
        #     if '発行済' in invalid:
        #         self.auPipe.update(tid=self.LOG_DATA[7], submit_status='211')
        #         return 0
        # return 1

    # 第三步 跳转至信息录入页面，并检测番号
    def top(self):
        print('in Login top')
        res = self.req.get(self.top_url)
        print(res.url)
        if res.url == self.login_url:
            raise AutomationError('登陆失效...')
        print('in Login top 2')
        res = self.req.get(self.add_url)
        assert res.url != self.login_url
        print('in Login top 3')
        reg = r'<input type="hidden" name="_PAGE_KEY" value="(.*?)" />'
        page_key = re.findall(reg, res.text)
        print(page_key)
        if len(page_key) == 0:
            raise AutomationError("_PAGE_KEY 没有")
        
        self._PAGE_KEY = page_key[0] 

        print('in Login top data')
        # 指定番号
        data = {
            'CHINA_AGENT_CODE': self.LOG_DATA[0]
        }

        res = self.req.post(self.agent_code_url, data=data)
        assert res.url != self.login_url
        print(res.json())
        if res.url == self.login_url:
            raise AutomationError('登陆失效...')
        try:
            self.res_info = res.json()
            print('指定番号检索完成(指定番号の検索完了)\n番号为(番号を)：\n\t{0}\nID为(IDを)：\n\t{1}\n'
                  '公司名(会社名)：\n\t{2}\n管辖公馆(管轄公館)：\n\t{3}'
                  ''.format(self.res_info['COMPANY_CODE'], self.res_info['CHINA_AGENT_ID'],
                            self.res_info['COMPANY_NAME'], self.res_info['DIPLOMAT_NAME']))
        except:
            raise AutomationError('未检测到番号')

    # 第四步 填写信息并确认

    def confirm(self):
        print('in login confirm')
        files = self.files_data()
        res = self.req.post(self.confirm_url, data=files)
        assert res.url != self.login_url
        if res.url == self.login_url:
            raise AutomationError('登陆失效...')
        reg = r'<input type="hidden" name="_PAGE_KEY" value="(.*?)" />'
        self._PAGE_KEY_2 = re.findall(reg, res.text)[0]

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
        except Exception as e:
            print(e)

        if res.url == 'https://churenkyosystem.com/member/identity_edit.php?mode=add' and res.status_code == 200:
            if '完了画面' not in res.text:
                raise AutomationError("未提交成功")
            try:
                reg = r'受付番号(.*?)<'
                self.FH = re.findall(reg, res.text)[0][1:].strip()
                print(f'\n\n===={self.FH}====\n\n')
            except Exception as e:
                print(e)
            if self.LOG_DATA[9] is None or self.LOG_DATA[9] == self.LOG_DATA[3]:
                update_data = {"tid": self.LOG_DATA[7], "submit_status": '211', "pdf": self.FH}
                self.auPipe.update(tid=self.LOG_DATA[7], submit_status='211', pdf=self.FH)
            else:
                update_data = {"tid": self.LOG_DATA[7], "submit_status": '222', "pdf": self.FH}
                self.auPipe.update(tid=self.LOG_DATA[7], submit_status='222', pdf=self.FH)
        else:
            if res.url == self.login_url:
                raise AutomationError('登陆失效, 重新登陆...')

        print('-' * 20, '\nthe info is OK\n', '-' * 20)
        print('提交数据OK\n')
        try:
            with open(os.path.join(LOG_DIR, f'{DAY()}.json'), 'a') as f:
                log = {'提交': self.LOG_DATA, 'id': self.FH,
                       'time': strftime('%m/%d %H:%M:%S')}
                json.dump(log, f)
                f.write(',\n')
        except:
            pass
        
        return update_data

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
            "ARRIVAL_DATE": self. LOG_DATA[4],
            "DEPARTURE_DATE": self.LOG_DATA[5],



            "_PAGE_KEY": self._PAGE_KEY,
            "BTN_CHECK_x": "確 認"
        }
        print('-------------------------')
        info = {
            '单次签证': 1,
            '三年多次签证': 10,
            '团体查证': 2,
            '冲绳三年签证': 3,
            '东北六县三年（青森）': 4,
            '东北六县三年（秋田）': 7,
            '东北六县三年（山形）': 8,
            '东北六县三年（岩手）': 5,
            '东北六县三年（宫城）': 6,
            '东北六县三年（福岛）': 9,
            '冲绳单次签证': 1,
            '东三县1三年': 6,
            '单次30': 1,
            '东北地区1': 1,
            '东北地区2': 12,
            '东北2A三年': 11,
            '东北2B三年': 13,
            '东北2C三年': 14,
            '东北2D三年': 14,
            '东三县2三年': 7,
            '冲绳东北六县多次': 10,
            '冲绳东北六县单次': 1,
            '东三县1单次': 1,
            '东三县2单次': 1,
            '东北六县单次（福岛）': 1,
            '东北六县单次（宫城）': 1,
            '东北六县单次（岩手）': 1,
            '东北六县单次（山形）': 1,
            '东北六县单次（秋田）': 1,
            '东北六县单次（青森）': 1,
            '普通，单次': 1,
            '足够经济能力人士，三年数次': 10,
            '宫城，单次': 1,
            '福岛，单次': 1,
            '岩手，单次': 1,
            '青森，单次': 1,
            '秋田，单次': 1,
            '山形，单次': 1,
            '宫城，三年数次': 6,
            '福岛，三年数次': 9,
            '岩手，三年数次': 5,
            '青森，三年数次': 4,
            '秋田，三年数次': 7,
            '山形，三年数次': 8,
            '冲绳，单次': 1,
            '冲绳，三年数次': 3,
        }

        add_info = info[self.LOG_DATA[6]]
        print(add_info)
        if add_info is 1:
            data["VISA_TYPE"] = '2'
            data["VISA_TYPE_1"] = '2'
            data["VISA_TYPE_2"] = '4'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 2:
            data["VISA_TYPE"] = '1'
            data["VISA_TYPE_1"] = '1'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 3:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_47"] = '47'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 4:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_2"] = '2'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 5:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_3"] = '3'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 6:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_4"] = '4'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 7:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_4"] = '5'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 8:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_6"] = '6'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 9:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_7"] = '7'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 10:
            data["VISA_TYPE"] = '4'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '4'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 11:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_2"] = '2'
            data["VISA_STAY_PREF_4"] = '5'
            data["VISA_STAY_PREF_6"] = '6'
            data["VISA_VISIT_TYPE"] = "0"
        elif add_info is 12:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_3"] = '3'
            data["VISA_STAY_PREF_4"] = '4'
            data["VISA_STAY_PREF_7"] = '7'
            data["VISA_VISIT_TYPE"] = '1'
            data["VISA_VISIT_PREF_3"] = '3'
            data["VISA_VISIT_PREF_4"] = '4'
            data["VISA_VISIT_PREF_7"] = '7'
        elif add_info is 13:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_2"] = '2'
            data["VISA_STAY_PREF_3"] = '3'
            data["VISA_STAY_PREF_4"] = '4'
            data["VISA_STAY_PREF_4"] = '5'
            data["VISA_STAY_PREF_6"] = '6'
            data["VISA_STAY_PREF_7"] = '7'
            data["VISA_VISIT_TYPE"] = '1'
            data["VISA_VISIT_PREF_3"] = '3'
            data["VISA_VISIT_PREF_4"] = '4'
            data["VISA_VISIT_PREF_7"] = '7'
        elif add_info is 14:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_47"] = '47'
            data["VISA_STAY_PREF_2"] = '2'
            data["VISA_STAY_PREF_4"] = '5'
            data["VISA_STAY_PREF_6"] = '6'
            data["VISA_VISIT_TYPE"] = '0'
        elif add_info is 15:
            data["VISA_TYPE"] = '3'
            data["VISA_TYPE_1"] = 'N'
            data["VISA_TYPE_2"] = '3'
            data["VISA_STAY_PREF_47"] = '47'
            data["VISA_STAY_PREF_2"] = '2'
            data["VISA_STAY_PREF_3"] = '3'
            data["VISA_STAY_PREF_4"] = '4'
            data["VISA_STAY_PREF_4"] = '5'
            data["VISA_STAY_PREF_6"] = '6'
            data["VISA_STAY_PREF_7"] = '7'
            data["VISA_VISIT_TYPE"] = '1'
            data["VISA_VISIT_PREF_3"] = '3'
            data["VISA_VISIT_PREF_4"] = '4'
            data["VISA_VISIT_PREF_7"] = '7'

        return data

    @property
    def run(self):
        update_data = {}
        try:
            self.top()
            self.confirm()
            self.con_two()
            print('=========')
        except AttributeError:
            update_data = {"tid": self.LOG_DATA[7], "status": '2'}
            self.auPipe.update(tid=self.LOG_DATA[7], status='2')
        except IndexError:
            update_data = {"tid": self.LOG_DATA[7], "status": '2'}
            self.auPipe.update(tid=self.LOG_DATA[7], status='2')
            raise AutomationError("列表超出范围", "automation_login")
        except AutomationError as ae:
            if ae.errorinfo == '未检测到番号':
                update_data = {"tid": self.LOG_DATA[7], "status": '8'}
                self.auPipe.update(tid=self.LOG_DATA[7], status='8')
            elif ae.errorinfo == "未提交成功":
                update_data = {"tid": self.LOG_DATA[7], "status": '9'}
                self.auPipe.update(tid=self.LOG_DATA[7], status='9')
            else:
                raise AutomationError('登陆失效, 重新登陆...', "automation_login")
            ERRINFO(self.LOG_DATA[7], self.LOG_DATA[1],
                    "automation_login", ae.errorinfo)
        except Exception as e:
            update_data = {"tid": self.LOG_DATA[7], "status": '2'}
            self.auPipe.update(tid=self.LOG_DATA[7], status='2')
            print('automation_login 出现错误...')
            ERRINFO(self.LOG_DATA[7], self.LOG_DATA[1], "automation_login", e)
            raise AutomationError(e, "automation_login")
        finally:
            return update_data
