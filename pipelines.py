import pymysql
import requests
# from DBUtils.PooledDB import PooledDB

import settings

travel_names = None
now_time = 0

class Mysql(object):
    """
    MYSQL数据库对象，负责产生数据库连接 , 此类中的连接采用连接池实现获取连接对象：conn = Mysql.getConn()
            释放连接对象;conn.close()或del conn
    """
    # 连接池对象
    __pool = None

    def __init__(self):
        self.getConn()

    def getConn(self):
        # 数据库构造函数，从连接池中取出连接，并生成操作游标
        # self._conn = Mysql.__getConn()
        self._conn = pymysql.connect(
            host=settings.DBHOST, port=settings.DBPORT,
            user=settings.DBUSER, passwd=settings.DBPWD,
            db=settings.DBNAME, use_unicode=True,
            charset=settings.DBCHAR  # , cursorclass=DictCursor
        )
        

    # @staticmethod
    # def __getConn():
    #     """
    #     @summary: 静态方法，从连接池中取出连接
    #     @return MySQLdb.connection
    #     """
    #     if Mysql.__pool is None:
    #         Mysql.__pool = PooledDB(
    #             creator=pymysql, mincached=1, maxcached=20,
    #             host=settings.DBHOST, port=settings.DBPORT,
    #             user=settings.DBUSER, passwd=settings.DBPWD,
    #             db=settings.DBNAME, use_unicode=True,
    #             charset=settings.DBCHAR  # , cursorclass=DictCursor
    #         )
    #     return Mysql.__pool.connection()

    def getAll(self, sql, param=None):
        """
        @summary: 执行查询，并取出所有结果集
        @param sql:查询 sql ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list(字典对象)/boolean 查询到的结果集
        """
        self._cursor = self._conn.cursor()
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchall()
        else:
            result = False
        self._cursor.close()
        return result

    def getOne(self, sql, param=None):
        """
        @summary: 执行查询，并取出第一条
        @param sql:查询 sql ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        self._cursor = self._conn.cursor()
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchone()
        else:
            result = False
        self._cursor.close()
        return result

    def getMany(self, sql, num, param=None):
        """
        @summary: 执行查询，并取出num条结果
        @param sql:查询 sql ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param num:取得的结果条数
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        self._cursor = self._conn.cursor()
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchmany(num)
        else:
            result = False
        self._cursor.close()
        return result

    def insertOne(self, sql, value):
        """
        @summary: 向数据表插入一条记录
        @param sql:要插入的 sql 格式
        @param value:要插入的记录数据tuple/list
        @return: insertId 受影响的行数
        """
        self._cursor = self._conn.cursor()
        self._cursor.execute(sql, value)
        self._cursor.close()
        return self.__getInsertId()

    def insertMany(self, sql, values):
        """
        @summary: 向数据表插入多条记录
        @param sql:要插入的 sql 格式
        @param values:要插入的记录数据tuple(tuple)/list[list]
        @return: count 受影响的行数
        """
        self._cursor = self._conn.cursor()
        count = self._cursor.executemany(sql, values)
        self._cursor.close()
        return count

    def __getInsertId(self):
        """
        获取当前连接最后一次插入操作生成的id,如果没有则为０
        """
        self._cursor = self._conn.cursor()
        self._cursor.execute("SELECT @@IDENTITY AS id")
        result = self._cursor.fetchall()
        self._cursor.close()
        return result[0]['id']

    def __query(self, sql, param=None):
        self._cursor = self._conn.cursor()
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        self._cursor.close()
        return count

    def update(self, sql, param=None):
        """
        @summary: 更新数据表记录
        @param sql:  sql 格式及条件，使用(%s,%s)
        @param param: 要更新的  值 tuple/list
        @return: count 受影响的行数
        """
        return self.__query(sql, param)

    def delete(self, sql, param=None):
        """
        @summary: 删除数据表记录
        @param sql:  sql 格式及条件，使用(%s,%s)
        @param param: 要删除的条件 值 tuple/list
        @return: count 受影响的行数
        """
        return self.__query(sql, param)

    def begin(self):
        """
        @summary: 开启事务
        """
        self._conn.autocommit(0)

    def end(self, option='commit'):
        """
        @summary: 结束事务
        """
        if option == 'commit':
            self._conn.commit()
        else:
            self._conn.rollback()

    def dispose(self, isEnd=1):
        """
        @summary: 释放连接池资源
        """
        if isEnd == 1:
            self.end('commit')
        else:
            self.end('rollback')
        self._conn.close()


def get_travel_names():
    global now_time
    global travel_names
    if not travel_names or settings.time() - now_time > 300:
        now_time = settings.time()
        mysql = Mysql()
        sql = "SELECT tid FROM dc_business_travel_setting WHERE partners=%s"
        travel_names = mysql.getAll(sql, settings.DJ_NAME)
        travel_names = tuple([i[0] for i in travel_names] + [0, 0])
        mysql.dispose()
    return travel_names


class AutomationPipelines(Mysql):
    '''数据库查询类
    '''

    def data(self):
        self.cur = self._conn.cursor()
        try:
            print('正在查询数据...')
            Undo = True

            sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf, ques, submit_status FROM dc_travel_business_list ' \
                f'WHERE submit_status=3 and travel_name in {get_travel_names()} and visa_type'
            self.cur.execute(sql)
            res_1 = self.cur.fetchone()
            if not res_1:
                for status in [1, 2]:
                    # 查证类别 出入境时间
                    sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf, ques, submit_status FROM dc_travel_business_list ' \
                        f'WHERE status = {status} and submit_status = 111 and travel_name in {get_travel_names()} and visa_type'
                    self.cur.execute(sql)
                    res_1 = self.cur.fetchone()
                    if res_1:
                        break
                else:
                    sql = f'SELECT travel_name, japan_entry_time, japan_exit_time, visa_type, exit_flight, tid, repatriation_pdf, ques, submit_status FROM dc_travel_business_list ' \
                        f'WHERE (status = 1 or status = 2) and travel_name in {get_travel_names()} and visa_type'
                    self.cur.execute(sql)
                    res_1 = self.cur.fetchone()
                    Undo = False
            if not res_1:
                print('无需要提交数据')
                return 0

            if res_1[8] == '222':
                self.update(tid=res_1[5], status='3')
                return 0
            if "五年" in res_1[3]:
                self.update(tid=res_1[5], status='5')
                return 0
                
            # 旅行社番号
            sql = f'SELECT travel_number, undertaker, calluser, calluser_phone, fex FROM dc_business_travel_setting WHERE tid = "{res_1[0]}"'
            self.cur.execute(sql)
            res_2 = self.cur.fetchone()
            if res_2 == ():
                print('res_2 未查到数据')
                return 0
            # 姓名，英文名 人数
            sql = f'SELECT username, english_name, english_name_s, COUNT(visa_id) FROM dc_travel_business_userinfo WHERE tvisa_id = "{res_1[5]}"'
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
            sql = 'SELECT username, english_name, english_name_s, sex, live_address, date_of_birth, passport_number, company_position FROM dc_travel_business_userinfo WHERE ' \
                'tvisa_id = "{}"'.format(res_1[5])
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
                res[3] = res[3][:6]
                res[4] = res[4].replace('-', '/').strip()

                res_info.append(res)
            self.res_info = res_info

            if '团' not in res_1[3] and self.log_data[0] not in settings.COMES:
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

        self.cur.close()
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
                status = status 『3 --> update_time = int(settings.time())』
            }
        '''
        self.cur = self._conn.cursor()

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
                        upSql = f"UPDATE dc_travel_business_list SET status='{status}', update_time={int(settings.time())} WHERE tid={tid};"
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
            self.cur.close()
            self.end()
        except:
            print('数据库执行出错, 进行回滚...')
            if not self.cur._closed:
                self.cur.close()
            self.end(0)

    def __del__(self):
        if hasattr(self, "cur"):
            self.cur.close()
        if hasattr(self, "_conn"):
            self.dispose()
