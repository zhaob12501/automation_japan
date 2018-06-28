# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 16:06:13 2018

@author: Administrator
"""

import xlwt
from settings import BASE_DIR, VISA


def cre_xls(LGO_INFO):
	workbook = xlwt.Workbook(encoding = 'ascii')
	worksheet = workbook.add_sheet('Worksheet')

	data = [
	        ('氏名', 'ピンイン', '性別', '居住地域', '生年月日', '旅券番号', '備考')
	        ]

	data = data + LGO_INFO
	print(data)
	for i in range(len(data)):
	    for j in range(len(data[i])):
	        worksheet.write(i, j, label = data[i][j])

	workbook.save(BASE_DIR + f'\\{VISA}.xls')
	print('xls文件准备完成!...')
	return 0
