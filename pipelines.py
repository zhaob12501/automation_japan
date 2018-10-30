import pymysql
import requests

from settings import DJ_NAME, time, COMES


class AutomationPipelines:
    '''数据库查询类
    '''

    def __init__(self, POOL):
        print('in AutomationPipelines...')
        self.con = POOL.connection()
        self.cur = self.con.cursor()
        print('连接成功...')

    def data(self):
        try:
            print('正在查询数据...')
            # 符合条件的旅行社
            sql = f"SELECT tid FROM dc_business_travel_setting WHERE partners='{DJ_NAME}'"
            self.cur.execute(sql)
            self.travel_name = self.cur.fetchall()
            self.travel_name = tuple([i[0] for i in self.travel_name] + [0, 0])
            Undo = True

            sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf, ques, submit_status FROM dc_travel_business_list \
                WHERE submit_status = 3 and travel_name in {self.travel_name} and visa_type not like "%五年%"'
            self.cur.execute(sql)
            res_1 = self.cur.fetchone()
            if not res_1:
                for status in [1, 2]:
                    # 查证类别 出入境时间
                    sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf, ques, submit_status FROM dc_travel_business_list \
                    WHERE status = {status} and submit_status = 111 and travel_name in {self.travel_name} and visa_type not like "%五年%"'
                    self.cur.execute(sql)
                    res_1 = self.cur.fetchone()
                    if res_1:
                        break
                else:
                    sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf, ques, submit_status FROM dc_travel_business_list \
                    WHERE (status = 1 or status = 2) and travel_name in {self.travel_name} and visa_type not like "%五年%"'
                    self.cur.execute(sql)
                    res_1 = self.cur.fetchone()
                    Undo = False
            if not res_1:
                print('无需要提交数据')
                return 0

            self.tid = res_1[5]

            if res_1[8] == '222':
                self.update(tid=self.tid, status='3')

            # 旅行社番号
            sql = f'SELECT travel_number, undertaker, calluser, calluser_phone, fex FROM dc_business_travel_setting WHERE tid = "{res_1[0]}"'
            self.cur.execute(sql)
            res_2 = self.cur.fetchone()
            if res_2 == ():
                print('res_2 未查到数据')
                return 0
            # 姓名，英文名 人数
            sql = f'SELECT username, english_name, english_name_s, COUNT(visa_id) FROM dc_travel_business_userinfo WHERE tvisa_id = "{self.tid}"'
            self.cur.execute(sql)
            res_3 = self.cur.fetchone()
            if res_1 == ():
                print('res_3 未查到数据')
                return 0

            # 查证信息
            self.log_data = (
                # 旅行社番号
                res_2[0],
                # 用户姓名
                res_3[0],
                # 用户英文姓名
                '{} {}'.format(res_3[1], res_3[2]),
                # 除去领队人数
                res_3[3] - 1,
                # 入境日期
                res_1[1].replace('-', '/').strip(),
                # 出境日期
                res_1[2].replace('-', '/').strip(),
                # 签证类型
                res_1[3],
                # tid
                res_1[5],
                # pdf
                res_1[6] if (not res_1[6]) or len(res_1[6]) == 9 else res_1[6].split(".pdf")[0][-9:],
                # 简版人数
                res_1[7] if not res_1[7] else res_1[7] - 1,
                # sub_status
                res_1[8],
            )
            if Undo:
                self.res_info = ()
                self.down_data = ()
                return 1
        except Exception as e:
            print('人员信息查询失败！')
            print(e, '\n人员信息查询失败！...')

        try:
            sql = 'SELECT username, english_name, english_name_s, sex, live_address, date_of_birth, passport_number, company_position FROM dc_travel_business_userinfo WHERE \
             tvisa_id = "{}"'.format(self.tid)
            self.cur.execute(sql)
            res_info = self.cur.fetchall()
            if res_info == ():
                print('res_info 未查到数据')
                return 0
            res_in = list(res_info)
            res_info = []

            m_f = {1: 0, 2: 0}

            for res in res_in:
                res = list(res)
                res = [str(i).strip() if i else '' for i in res]
                name = res.pop(2)
                res[1] = f'{res[1]} {name}' if len(
                    f'{res[1]} {name}') < 16 else f'{res[1]}{name}'
                res[2] = 1 if res[2] == '男' else 2
                m_f[res[2]] += 1
                res[4] = res[4].replace('-', '/').strip()

                res = tuple(res)
                res_info.append(res)
            self.res_info = res_info

            if '团' not in res_1[3] and self.log_data[0] not in COMES:
                self.down_data = ()
                return 1

        except Exception as e:
            print('in res_info error')
            print(e, '\n需要的提交表格数据查询失败！...')

        try:
            sql = f'select flight_name, originating_place, start_time, destination, stop_time from dc_business_tavel_fly where flight_name ="{res_1[4]}" AND fmpid = 0'
            self.cur.execute(sql)
            res_4 = self.cur.fetchone()
            if not res_4:
                print('res_4 未查到数据')
                self.down_data = ('', '', '', '', '', '',
                                  '', '', '', '', '', '', '')
                return 1
            self.down_data = (
                res_2[1], res_2[3], res_2[4], res_2[2], m_f[2], m_f[1],
                res_4[0], res_4[1][:2], res_4[2], res_4[3][:2], res_4[4],
            )

            m_f = {1: 0, 2: 0}
        except Exception as e:
            print('归国报告数据查询失败！')
            print(e, '归国报告数据查询失败！...')

        return 1

    def update(self, tid='', status='', submit_status='', pdf=''):
        '''修改数据库接口
            参数:
                tid
                status {'2', '3', '7', '8'}
                submit_status {'211', '221', '222', '111'}
                pdf '{番号}'

            submit_status = 211 --> {
                3   --> repatriation_pdf = pdf
                111 --> repatriation_pdf = pdf, submit_status = submit_status
            }

            submit_status = 221 or 222 --> {
                3   --> 跳过
                211 --> repatriation_pdf = pdf, submit_status = submit_status, status = status
            }

            submit_status = 111 --> {
                3   --> repatriation_pdf = '', submit_status = 111, status = 7
            }

            status = 8, 9, 2, 3 --> {
                status = status 『3 --> update_time = int(time())』
            }
        '''
        sql = f"SELECT status, submit_status, repatriation_pdf FROM dc_travel_business_list where tid = {tid}"
        self.cur.execute(sql)
        res = self.cur.fetchone()
        if not res:
            return 0
        try:
            if res[1] != '3' and res[0] not in [0, 6, 7]:
                if status:
                    if str(status) != '3':
                        upSql = f"UPDATE dc_travel_business_list SET status='{status}' WHERE tid={tid};"
                    else:
                        upSql = f"UPDATE dc_travel_business_list SET status='{status}', update_time={int(time())} WHERE tid={tid};"

                    self.cur.execute(upSql)
                if pdf:
                    upSql = f"UPDATE dc_travel_business_list SET repatriation_pdf='{pdf}' WHERE tid={tid};"
                    self.cur.execute(upSql)
                if submit_status:
                    upSql = f"UPDATE dc_travel_business_list SET submit_status='{submit_status}' WHERE tid={tid};"
                    self.cur.execute(upSql)
            elif res[1] == '3':
                if submit_status == '111':
                    if res[0] == 1:
                        upSql = f"UPDATE dc_travel_business_list SET repatriation_pdf='', repatriations_pdf='', submit_status='111' WHERE tid={tid};"
                    else:
                        upSql = f"UPDATE dc_travel_business_list SET status='7', repatriation_pdf='', repatriations_pdf='', submit_status='111' WHERE tid={tid};"
                    self.cur.execute(upSql)
                elif submit_status in ['221', '222'] and not res[2] and pdf:
                    upSql = f"UPDATE dc_travel_business_list SET repatriation_pdf='{pdf}' WHERE tid={tid};"
                    self.cur.execute(upSql)
            elif res[0] in [6, 7] and submit_status == '211':
                upSql = f"UPDATE dc_travel_business_list SET status='6', submit_status='3', repatriation_pdf='{pdf}' WHERE tid={tid};"
                self.cur.execute(upSql)

            self.con.commit()
        except:
            print('数据库执行出错, 进行回滚...')
            self.con.rollback()

    def __del__(self):
        print('\n数据库正在关闭连接')
        if hasattr(self, "cur"):
            self.cur.close()
        if hasattr(self, "con"):
            self.con.close()
        print('数据库已关闭连接\n')
