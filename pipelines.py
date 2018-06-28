import pymysql
from settings import DJ_NAME, POOL


class AutomationPipelines:
    def __init__(self):
        print('in SQL...')
        self.con = POOL.connection()
        self.cur = self.con.cursor()
        print('连接成功...')
        self.get_travel_name()

    def get_travel_name(self):
        # 符合条件的旅行社
        sql = f"SELECT tid FROM dc_business_travel_setting WHERE partners='{DJ_NAME}'"
        self.cur.execute(sql)
        self.travel_name = self.cur.fetchall()
        self.travel_name = tuple([i[0] for i in self.travel_name] + [0])
        print('符合条件的 travel_name:', self.travel_name)

    @property
    def get_res(self):
        print('in get_res...')
        sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf FROM dc_travel_business_list WHERE (status = 1 or status = 2 or submit_status = 3) and travel_name in {self.travel_name}'
        self.cur.execute(sql)
        if self.cur.fetchall():
            print('有数据, 准备提交签证...')
            return 0
        print('没有数据...')
        return 1

    def undo_p(self):
        try:
            print('in undo_p')
            # 符合条件的旅行社
            # sql = f"SELECT tid FROM dc_business_travel_setting WHERE partners='{DJ_NAME}'"
            # self.cur.execute(sql)
            # self.travel_name = self.cur.fetchall()
            # self.travel_name = tuple([i[0] for i in self.travel_name])

            # 查证类别 出入境时间
            sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf FROM dc_travel_business_list WHERE submit_status = 3 and travel_name in {self.travel_name}'
            self.cur.execute(sql)
            res_1 = self.cur.fetchone()
            if not res_1:
                print('无撤销数据')
                return 0
            # print(res_1)
            # 旅行社番号
            sql = 'SELECT travel_number, undertaker, calluser, calluser_phone, fex FROM dc_business_travel_setting WHERE tid = "{}"'.format(
                res_1[0])
            self.cur.execute(sql)
            res_2 = self.cur.fetchone()

            # 姓名，英文名 人数
            sql = 'SELECT username, english_name, english_name_s, COUNT(visa_id) FROM dc_travel_business_userinfo WHERE tvisa_id = "{}"'.format(
                res_1[5])
            self.cur.execute(sql)
            res_3 = self.cur.fetchone()
            
            # 查证信息
            self.undo_data = (
                res_2[0],
                res_3[0],
                '{} {}'.format(res_3[1], res_3[2]),
                res_3[3] - 1,
                res_1[1].replace('-', '/').strip(),
                res_1[2].replace('-', '/').strip(),
                res_1[3],
                res_1[5],
                res_1[6]
            )
            print(self.undo_data)
            return 1
        except Exception as e:
            print(e, '\n签证人员信息查询失败！...')
            return 0

    def data(self):
        try:
            print('in data log_data...')
            # print(DJ_NAME)
            # # 查询符合条件的旅行社
            # sql = f"SELECT tid FROM dc_business_travel_setting WHERE partners='{DJ_NAME}'"
            # self.cur.execute(sql)
            # self.travel_name = self.cur.fetchall()
            # self.travel_name = tuple([i[0] for i in self.travel_name])

            # 查证类别 出入境时间
            sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf, ques FROM dc_travel_business_list WHERE status = 1 and travel_name in {self.travel_name}'
            self.cur.execute(sql)
            res_1 = self.cur.fetchone()

            if not res_1:
                sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf, ques FROM dc_travel_business_list WHERE status = 2 and travel_name in {self.travel_name}'
                self.cur.execute(sql)
                res_1 = self.cur.fetchone()
                if not res_1:
                    print('无需要提交数据')
                    return 0
            self.tid = res_1[5]
            # 旅行社番号
            sql = 'SELECT travel_number, undertaker, calluser, calluser_phone, fex FROM dc_business_travel_setting WHERE tid = "{}"'.format(
                res_1[0])
            self.cur.execute(sql)
            res_2 = self.cur.fetchone()
            if res_2 == ():
                print('res_2 未查到数据')
                return 0
            # 姓名，英文名 人数
            sql = 'SELECT username, english_name, english_name_s, COUNT(visa_id) FROM dc_travel_business_userinfo WHERE tvisa_id = "{}"'.format(
                self.tid)
            self.cur.execute(sql)
            res_3 = self.cur.fetchone()
            if res_1 == ():
                print('res_3 未查到数据')
                return 0

            # res_1 = list(res_1)
            # try:
            #     res_1[7] = int(res_1[7]) if int(res_1[7]) > 0 else None
            # except:
            #     res_1[7] = None

            # 查证信息
            self.log_data = (
                res_2[0], 
                res_3[0], 
                '{} {}'.format(res_3[1], res_3[2]), 
                res_3[3] - 1 if not res_1[7] else res_1[7] - 1,
                res_1[1].replace('-', '/').strip(), 
                res_1[2].replace('-', '/').strip(), 
                res_1[3],
                res_1[5],
                res_1[6],
                res_1[7],
            )
            print(self.log_data)
            if res_1[7]:
                self.res_info = ()
                self.down_data = ()
                return 1

        except Exception as e:
            print('in log data error')
            print(e, '\n签证人员信息查询失败！...')

        try:
            sql = 'SELECT username, english_name, english_name_s, sex, live_address, date_of_birth, passport_number, company_position FROM dc_travel_business_userinfo WHERE tvisa_id = "{}"'.format(
               self.tid)
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
                res[1] = f'{res[1]} {name}' if len(f'{res[1]} {name}') < 16 else f'{res[1]}{name}'
                res[2] = 1 if res[2] == '男' else 2
                m_f[res[2]] += 1
                res[4] = res[4].replace('-', '/').strip()


                res = tuple(res)
                res_info.append(res)
            self.res_info = res_info

            if '团' not in res_1[3]:
                self.down_data = ()
                return 1

        except Exception as e:
            print('in res_info error')
            print(e, '\n需要的提交表格数据查询失败！...')

        try:
            sql = 'select flight_name, originating_place, start_time, destination, stop_time from dc_business_tavel_fly where flight_name ="{}" AND fmpid = 0'.format(
                res_1[4])
            self.cur.execute(sql)
            res_4 = self.cur.fetchone()
            if not res_4:
                print('res_4 未查到数据')
                self.down_data = ('', '', '', '', '', '', '', '', '', '', '', '', '')
                return 1
            self.down_data = (
                res_2[1], res_2[3], res_2[4], res_2[2], m_f[2], m_f[1],
                res_4[0], res_4[1][:2], res_4[2], res_4[3][:2], res_4[4],
            )

            m_f = {1: 0, 2: 0}
        except Exception as e:
            print('in down data error')
            print(e, '归国报告数据查询失败！...')

        return 1

    def status(self, tid):
        sql = f'SELECT submit_status FROM dc_travel_business_list where tid = {tid}'
        self.cur.execute(sql)
        res = self.cur.fetchone()[0]
        return res

    def __del__(self):
        print('\n数据库正在关闭连接')
        self.cur.close()
        self.con.close()
        print('数据库已关闭连接\n')


if __name__ == '__main__':
    pass
    # p = AutomationPipelines()
    # print(p.undo_p())
    # # print(p.undo_data)
    # print(p.data())
    # print(p.log_data, p.res_info, p.down_data, sep='\n')
