import calendar
import datetime

import pulp
import csv

# * リスト
# M: ナースの集合
# M = list(range(1, 9))
M = ['鬼原', '佐藤', '鈴木', '高橋', '柴田', '田中', '伊藤', '渡辺']
# D: 日付の集合
# D = list(range(1, 30))
# D = list(range(1, 30))
year = 2023  # 年
month = 11  # 月
# 日付の集合作成
D = []
for i in range(calendar.monthrange(year, month)[1]):
    D.append(datetime.date(year, month, i+1))

# C: 勤務区分の集合
C = ['/', 'D', 'N']  # C[0]: 休み C[1]: 昼勤 C[2]: 夜勤
# Q: 禁止シフト1
Q = ['ND', '/D/', '/N/']
# Q: 禁止シフト2
Q2 = ['DDDD/D', 'DDDD/N', 'DDDN/D', 'DDDN/N', 'DDNN/D', 'DDNN/N', 'DNNN/D', 'DNNN/N', 'NNNN/D', 'NNNN/N']

problem = pulp.LpProblem(sense=pulp.LpMinimize)

# 変数
# x[i, j, k]: ナース番号iがj日の勤務kであるかどうか
x = pulp.LpVariable.dicts('x', [(m, d.day, c) for m in M for d in D for c in C], cat='Binary')
# y[i, j]: ナース番号iがj番目の週末に休暇をとるかどうか
y = pulp.LpVariable.dicts('y', [(m, i) for m in M for i in [0, 1]], cat='Binary')

# その日の勤務は休み、昼勤、夜勤のどれか1つ
for m in M:
    for d in D:
        problem += pulp.lpSum([x[m, d.day, c] for c in C]) == 1
# 制約(0)
# 各日の各シフトにおいて、2人のナースが勤務しなければならない
# ok
for d in D:
    for c in C[1:]:
        problem += pulp.lpSum([x[m, d.day, c] for m in M]) == 2
    # 制約(1)
# 休みを7回以上確保する
for m in M:
    problem += pulp.lpSum([x[m, d.day, C[0]] for d in D]) >= 7

# 制約(2)
# 週末(土日)連休を1回以上確保する
SatDate = []  # 土曜の日付取得
SunDate = []  # 日曜の日付取得
for i in D:
    if i.strftime('%a') == 'Sat':
        SatDate.append(i.day)
    if i.strftime('%a') == 'Sun':
        SunDate.append(i.day)

for m in M:
    problem += pulp.lpSum([y[m, i] for i in [0, 1]]) >= 1
    problem += x[m, SatDate[0], C[0]] + x[m, SunDate[0], C[0]] == y[m, 0] * 2
    problem += x[m, SatDate[1], C[0]] + x[m, SunDate[1], C[0]] == y[m, 1] * 2
"""
for m in M:
    problem += pulp.lpSum([y[m, i] for i in [0, 1]]) >= 1
    problem += x[m, 6, C[0]] + x[m, 7, C[0]] == y[m, 0] * 2
    problem += x[m, 13, C[0]] + x[m, 14, C[0]] == y[m, 1] * 2
"""

# 制約(3)
# 連続勤務は4日までしか許されない
for m in M:
    for d in D[4:]:
        problem += pulp.lpSum([x[m, d.day - h, c] for h in range(4 + 1) for c in C[1:]]) <= 4

# 制約(4)
# 夜勤の翌日の日勤は許されない
q0 = Q[0]
t = len(q0) - 1
for m in M:
    for d in D[t:]:
        problem += pulp.lpSum([x[m, d.day - t + h, q0[h]] for h in range(t + 1)]) <= t
# 制約(5)
# 夜勤は3日連続までしか許されない
for m in M:
    for d in D[3:]:
        problem += pulp.lpSum([x[m, d.day - h, C[2]] for h in range(3 + 1)]) <= 3

# ----- 条件6からは可能であればの条件。
# 制約(6)
# 前後が休みになる孤立勤務を避ける
for m in M:
    for q in Q[1:]:
        t = len(q) - 1
        for d in D[t:]:
            problem += pulp.lpSum([x[m, d.day - t + h, q[h]] for h in range(t + 1)]) <= t
# 制約(7)
# 4連続勤務を避ける。避けられない場合は直後の2日間を休みにする
# * 4連続勤務の場合、増える何かを作って最小化すれば良いと思う...
for m in M:
    for q in Q2:
        t = len(q) - 1
        for d in D[t:]:
            problem += pulp.lpSum([x[m, d.day - t + h, q[h]] for h in range(t + 1)]) <= t

pulp.LpStatus[problem.solve()]

# print(' , 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14, /, D, N,週末')
Member = []
PeopleCount = []
for p in M:
    buf = [p]
    for d in D:
        for c in C:
            if x[p, d.day, c].value():
                buf.append(f'{c}')
    # print(f"{p},{','.join(buf)},{buf.count(' /'): 2d},{buf.count(' D'): 2d},{buf.count(' N'): 2d}, {int(y[p,
    # 0].value()):d}{int(y[p, 1].value()):d}")
    Member.append(buf)
for c in C[1:]:
    buf = [c]
    for d in D:
        buf.append(f" {str(int(sum([x[p, d.day, c].value() for p in M])))}")
    # print(f"{c}:{','.join(buf)}")
    PeopleCount.append(buf)

with open('data.csv', 'wt', encoding='utf-8', newline="") as f:
    # ライター（書き込み者）を作成
    writer = csv.writer(f)

    DateList = [f'{year}年{month}月']
    WeekList = ['曜日']

    for i in D:
        DateList.append(i.day)
        WeekList.append(i.strftime('%a'))
    # ライターでデータ（リスト）をファイルに出力
    writer.writerow(DateList)
    writer.writerow(WeekList)

    for i in Member:
        writer.writerow(i)
