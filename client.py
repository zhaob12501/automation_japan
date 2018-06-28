import os
import sqlite3
import subprocess
from os import getenv

import requests
from pykeyboard import PyKeyboard
from pymouse import PyMouse

import win32crypt
from settings import *


def getCookies():  
    conn = sqlite3.connect(getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default\\Cookies")  
    cursor = conn.cursor()  
    #cursor.execute('select host_key,name,encrypted_value from cookies where host_key like "%test%"')  
    cursor.execute('select host_key,name,encrypted_value from cookies where host_key like "churenkyosystem.com"')
    cookies={}  
    for result in cursor.fetchall():  
        # print(result)    
        value = win32crypt.CryptUnprotectData(result[2], None, None, None, 0)[1]
        # print(result[2], value)  
        if value != b'""':  
            cookies[result[1]] = value.decode('utf8')
        elif not value:  
           print("no password found")  
    cursor.close()
    return cookies


# 第一步 打开exe登录
def open_client():
    pname = EXE_PWD
    subprocess.Popen(pname)
    m = PyMouse()
    k = PyKeyboard()
    sleep(2)
    m.click(COORDINATES_1[0],COORDINATES_1[1])
    sleep(2)
    k.type_string(PASSWD_EXE)
    sleep(2)
    m.click(COORDINATES_2[0],COORDINATES_2[1])
    sleep(60)
    # try:
    #     os.system('taskkill /F /IM chrome.exe')
    # except:
    #     pass



class ClientLogin:
    def __init__(self):
        self.req = requests.Session()
        # self.req.proxies = {'http': '127.0.0.1:8888'}
        # self.verify = False
        _cookies = getCookies()
        
        co = _cookies
        try:
            co.pop('PHPSESSID')
        except:
            pass
        print(co)
        requests.utils.add_dict_to_cookiejar(self.req.cookies, co)

        self.req.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
            }
        # 登录1
        # self.log_url = 'https://churenkyosystem.com/securemagic/login.php'

        # 登录页面url
        self.login_url = 'https://churenkyosystem.com/member/login.php'
        # top页面url
        self.top_url = 'https://churenkyosystem.com/member/top.php'

        self.req.get(self.login_url)
        # requests.utils.add_dict_to_cookiejar(self.req.cookies, _cookies)

    # 第二步 登录（网页登录）
    def login(self):
        from_data = {
            'LOGIN_ID': LOGIN_ID,
            'PASSWORD': PASSWORD,
            'SUBMIT_LOGIN_x': 'ログイン'
         }
        # print(from_data)
        print('正在传输,请耐心等待...')
        sleep(5)
        res = self.req.post(self.login_url, data=from_data)
        print(res.url)
        if res.url == self.top_url:
            # print('登录成功!...\n')
            return 1
        else:
            # print('登录失败！...请重试！...')
            return 0

    def refresh(self, req):
        res = req.get(self.top_url)
        print(res.url)
        if res.url == self.login_url:
            for _ in range(5):
                if self.login():
                    break
            else:
                return 1
        return 0
                
            
        
    @property
    def run(self):
        for _ in range(5):
            if self.login():
                break
            sleep(10)
            return 0
        else:
            return 1

