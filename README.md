# automation_japan

**日本签证自动化录入系统**

```python
# 更新时间: 2018-6-28
```

> `automation_run.py` 运行主程序，逻辑控制模块
>
> `settings.py` 全局设置，所有需要用到的全局变量都在这里。如：地接资料信息（从path/ user_pwd.txt 中读取）、数据库信息等。(未提交至远程仓库)
>
> `client.py` 操作EXE程序登录，获取 Chrome Cookie 值，进行携带 Cookie 模拟登录
>
> `pipelines.py` 数据库查询操作，对需要提交或撤回的消息进行查询，并返回需要操作的数据
>
> `automation_login.py` 进行数据提交，将数据提交至日本使馆官网
>
> `automation_transmission.py` 对数据的 xls 文件进行上传
>
> `create_xls.py` 对需要上传的数据进行 xls 生成
>
> `automation_download.py` 如果是团体签证，则下载归国报告书，上传至魔派官网
>
> `automation_undo.py` 执行撤销操作



**打包:**

```python
# pip install pyinstaller

# 有小黑框
$ pyinstaller -F -i abc.ico automation_run.py automation_login.py automation_transmission.py automation_download.py automation_undo.py create_xls.py client.py pipelines.py settings.py

# 无小黑框
$ pyinstaller -F -w -i abc.ico automation_run.py automation_login.py automation_transmission.py automation_download.py automation_undo.py create_xls.py client.py pipelines.py settings.py
```





## 遇到并解决的问题:

### 数据库长连接:

**问题:**

```python
# 每次请求数据库, 都会重新建立连接, 执行查询操作, 非常耗费资源
# 而且一旦数据库连接异常, 程序就会卡死, 所以需要确保数据库连接正常
```
**解决方法:**

```python
# 使用 DBUtils 模块, 数据库连接池, 解决 参考: http://www.vuln.cn/8627
# 安装: pip install dbutils
# demo
import pymysql
from DBUtils.PooledDB import PooledDB


pool = PooledDB(
	pymysql,
	5, # 5为连接池里的最少连接数
	host='localhost',
	user='root',
	passwd='pwd',
	db='myDB',
	port=3306,
	charset="utf8"
	) 
	
conn = pool.connection() #以后每次需要数据库连接就是用connection（）函数获取连接就好了
cur=conn.cursor()
SQL="select * from table1"
r=cur.execute(SQL)
r=cur.fetchall()
cur.close()
conn.close()
```

