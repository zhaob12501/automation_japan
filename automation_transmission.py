import json
import os
import re

import requests

import client
import create_xls
from settings import *


class Transmission:
    def __init__(self, req, LOG_DATA, LOG_INFO):
        self.req = req
        # requests.utils.add_dict_to_cookiejar(self.req.cookies, client.getCookies())
        self.LOG_DATA = LOG_DATA
        self.LOG_INFO = LOG_INFO
        # self.req.proxies = {'http': '127.0.0.1:8888', 'https': '127.0.0.1:8888'}
        # self.req.verify = False
        self.identity_list_url = 'https://churenkyosystem.com/member/identity_list.php'
        self.identity_name_url = 'https://churenkyosystem.com/member/identity_name_list.php?IDENTITY_ID={}'
        self.i_nup_e_url = 'https://churenkyosystem.com/member/identity_nameupload_edit.php?IDENTITY_ID={}'
        # self.info = '{0}（{1}）：{2}名'.format(self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[3])
        if self.LOG_DATA[3] == self.LOG_DATA[9] or self.LOG_DATA[9] is None:
            self.info = '{0}（{1}）：{2}名'.format(self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[3])
        else:
            self.info = '{0}（{1}）：{2}名'.format(self.LOG_DATA[1], self.LOG_DATA[2], self.LOG_DATA[9])
        print(self.info)
        # 登录页面url
        self.login_url = 'https://churenkyosystem.com/member/login.php'

        print('开始准备提交数据')

    # 1、 进入搜索信息搜索列表，并搜索指定ID
    def search_info(self):
        print('进入搜索信息搜索列表，并搜索指定ID')
        print(self.LOG_DATA[8])
        if self.LOG_DATA[8]:
            print('检索信息-有番号查询')
            data = {
                'CODE': self.LOG_DATA[8],
                'PAGE_VIEW_NUMBER': '0',
                'BTN_SEARCH_x': '検 索',
            }

            res = self.req.post(self.identity_list_url, data=data)
            reg = r'<a href="identity_info\.php\?IDENTITY_ID=(.*?)">{}</a>'.format(self.LOG_DATA[8])
            self.identity_id = re.findall(reg, res.text)[0]
            print('The Transmission first step to success!')
            print(self.identity_id)
        else:
            # 1、 进入搜索信息搜索列表，并搜索指定ID
            # def search_info(self):
            print('检索信息-无番号查询')
            try:
                res = self.req.get(self.identity_list_url)
                if res.url == self.login_url:
                    c = client.ClientLogin()
                    c.run
                    self.req = c.req
                    res = self.req.get(self.identity_list_url)
                self.identity_id = res.text.split(self.info, 1)[1].split('<tr class="', 1)[1].split('"', 1)[0][-7:]
                print('The Transmission first step to success!')
                print(self.identity_id)
                    
            except:
                for i in range(1, 21):
                    ne = '?p={}&s=1&d=2'.format(i)
                    url = self.identity_list_url + ne
                    res = self.req.get(url)
                    if res.url == self.login_url:
                        c = client.ClientLogin()
                        c.run
                        self.req = c.req
                        res = self.req.get(url)
                    try:
                        self.identity_id = res.text.split(self.info, 1)[1].split('<tr class="', 1)[1].split('"', 1)[0][-7:]
                        print('The Transmission first step to success!')
                        self.get_url = url
                        break
                    except:
                        continue
                else:
                    print('Your records are too old. Please resubmit your information!...')
     
    def upload_one(self):
        
        url = self.identity_name_url.format(self.identity_id)

        res = self.req.get(url)
        reg = '<tr><th>受付番号</th><td colspan="3">(.*?)</td></tr>'
        self.FH = re.findall(reg, res.text)[0]

        print('The Transmission second step is successful')
        url = self.i_nup_e_url.format(self.identity_id)
        res = self.req.get(url)
        if not self.FH:
            self.FH = re.findall(reg, res.text)[0]
        
        if not self.LOG_DATA[8]:
            url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanInsertPdftext'
            data = {'tid': self.LOG_DATA[7], 'text': self.FH}
            requests.post(url, data=data).json()

        if res.url == self.login_url:
            c = client.ClientLogin()
            c.run
            self.req = c.req
            res = self.req.get(url)
        print('The Transmission third step is successful!\n')
        reg = '<input type="hidden" name="_PAGE_KEY" value="(.*?)" />'
        self._PAGE_KEY = re.findall(reg, res.text)[0]
        
        

    def upload_two(self):
        print('开始提交')
        url = self.i_nup_e_url.split('?')[0]
        #header_up['Referer'] = str('https://churenkyosystem.com/member/identity_list.php'),
        data = {
            "IDENTITY_ID": self.identity_id,
            "_PAGE_KEY": self._PAGE_KEY,
            "BTN_SUBMIT_x": "登 録",
        }
        
        # 创建表格
        create_xls.cre_xls(self.LOG_INFO)
        
        files = {"CSV_FILE": (f'{VISA}.xls', open(BASE_DIR + f'\\{VISA}.xls', 'rb'), 'application/vnd.ms-excel')}
        res = self.req.post(url, data=data, files=files)
        if '登録が完了しました' not in res.text:
            japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
            data = {'tid': self.LOG_DATA[7], 'status': '2'}
            res = requests.post(japan_url, data=data).json()
            return -1 
        try:
            
            print('-' * 20, '\nThe Transmission fourth step is successful\n', '-' * 20)
            print('\tFile upload successful!')
            print('\n===xls文件上传完成OK===\n\n')
            if '团体' not in self.LOG_DATA[6]:
                japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
                data = {'tid': self.LOG_DATA[7], 'status': '3', 'submit_status': '222'}
                res = requests.post(japan_url, data=data).json()
                print(res, '提交完成！\n========\n', sep='\n')
 
            else:
                japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
                data = {'tid': self.LOG_DATA[7], 'submit_status': '221'}
                res = requests.post(japan_url, data=data).json()
                print(res)
            return 1
        except:
            return -1
    @property
    def run(self):
        try:
            self.search_info()
        except:
            japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
            data = {'tid': self.LOG_DATA[7], 'status': '2'}
            res = requests.post(japan_url, data=data).json()
        sleep(1)

        try:
            self.upload_one()
        except:
            japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
            data = {'tid': self.LOG_DATA[7], 'status': '2'}
            res = requests.post(japan_url, data=data).json()
        sleep(1)

        try:
            s = self.upload_two()
            if s == 1:
                print(self.LOG_DATA[6])
                try:
                    with open(os.path.join(LOG_DIR, f'{DAY()}.json'), 'a') as f:
                        log = {'xls提交': self.LOG_INFO, 'time': strftime('%m/%d %H:%M:%S')}
                        json.dump(log, f)
                        f.write(',\n')
                except:
                    pass
        except Exception as e:
            print('automation_transmission 出现错误...')
            with open(BASE_DIR + '\\visa_log/error.json', 'a') as f:
                f.write(f'["automation_transmission", "{strftime("%Y-%m-%d %H:%M:%S")}", "{e}"],\n')
            japan_url = 'http://www.mobtop.com.cn/index.php?s=/Api/MalaysiaApi/japanVisaStatus'
            data = {'tid': self.LOG_DATA[7], 'status': '2'}
            res = requests.post(japan_url, data=data).json()
            assert 'transmission error' == '' 
        sleep(1)
        

if __name__ == '__main__':
    pass
