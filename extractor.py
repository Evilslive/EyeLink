#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import re
import numpy as np

def d(decimal): # 小數點轉整數(ms)
    return int(float(decimal))

def cost_time(start, end): # 每篇花費時間
    for i in range(len(start)):
        t = int((end[i] - start[i])/1000)
        print("第 {:>2d} 篇, {:d} 秒".format(i+1, t))

def write_down(data:list, name):
    with open(name+".txt", 'a', errors="replace") as w:
        for i in data:
            w.writelines("\t".join(i)+"\n")

#_________________________________ DATA EXTRACTION _________________________________

def read_asc(path):
    '''
        OUTPUT:
    '''
    #res_x, res_y = [], [] # resolution
    #aoi_x, aoi_y = [], [] # area of interest
    note = [] # annotation
    msg = []  # system information
    # store time series data, when & where, eye gaze location, (x, y), number of missing location
    location, loc_x, loc_y, loc_p, miss_point, start_time, end_time = [], [], [], [], 0, 0, 0
    # from SR Research, [start, end, duration, go_x, go_y, from_x, from_y, ...]
    saccade, sac_du, sac_x1, sac_y1, sac_x0, sac_y0  = [], [], [], [], [], []
    # from SR Research, [start, end, duration, loc_x, loc_y, pupil, ...]
    fixation, fix_du, fix_lx, fix_ly, fix_pp = [], [], [], [], [] 
    with open(path, 'r', errors="replace") as f:
        pages = f.readlines()
        for i in pages:
            i = re.split("\t|\n", i)
            header = i[0][:3]

            if header.isnumeric(): # int for data
                if "   ." in i: # miss trial
                    miss_point += 1
                else:
                    loc_x.append(float(i[1]))
                    loc_y.append(float(i[2]))
                    loc_p.append( d(i[3]))

            elif header == "ESA":
                if "   ." not in i:
                    sac_du.append(float(i[4]))
                    sac_x1.append(float(i[5]))
                    sac_y1.append(float(i[6]))
                    sac_x0.append(float(i[7]))
                    sac_y0.append(float(i[8]))

            elif header == "EFI":
                if "   ." not in i:
                    fix_du.append(float(i[4]))
                    fix_lx.append(float(i[5]))
                    fix_ly.append(float(i[6]))
                    fix_pp.append(float(i[7]))

            elif header == "** ":
                note.append(i[3:-1]) # cut the last "\n"

            elif header == "MSG":
                msg.append(i[1:-1])

            elif header == "STA":
                start_time = d(i[1])

            elif header == "END":
                end_time = d(i[1])
                # raw
                location.append([loc_x, loc_y, loc_p, miss_point, end_time-start_time])
                loc_x, loc_y, loc_p, miss_point, start_time, end_time = [], [], [], 0, 0, 0
                # 
                fixation.append([fix_lx, fix_ly, fix_du, fix_pp])
                fix_lx, fix_ly, fix_du, fix_pp = [], [], [], []
                #
                saccade.append([sac_x0, sac_y0, sac_x1, sac_y1, sac_du]) # 位置已轉換
                sac_x0, sac_y0, sac_x1, sac_y1, sac_du = [], [], [], [], []

    #write_down(note, "subj")
    #write_down(msg, "subj")
    return location, fixation, saccade

#_________________________________ AREA OF INTEREST _________________________________

def road_IA(path):
    f_list = os.listdir(path)
    f_list.sort(key=lambda e:int(e.replace("IA_",'').replace(".ias",'')))
    coordinate = [] # text boundaries
    text_box = []
    for i in f_list: # each articles
        temp_r, temp_c = [], []
        one_row = []
        with open(path+i, 'r', errors="ignore") as f:
            page = f.readlines()

            # Assume height of each row is fixed
            for row in page:
                row = re.split("\n|\t", row)
                left, up, right, down = map(int, row[2:6])

                if up not in temp_r:
                    temp_r.append(up)

                if down not in temp_r:
                    temp_r.append(down)

                if temp_c != [] and left < temp_c[-1][0]:
                    one_row.append(temp_c)
                    temp_c = [] # new row
                temp_c.append([left, right,(int(row[1]), row[6])])
                # [左界, 右界, (序, WORD)]
            one_row.append(temp_c)
            #tempR.sort() # just in case
            coordinate.append(temp_r)
            text_box.append(one_row)
    
    return coordinate, text_box

#_________________________________ GAZE _________________________________

# fixation與gaze所取得的資料差異甚微, 相關約.98以上
# calculate the accumulated gaze time
def accumulate_fix_time(rows, text_box, x, y, duration=None): 
    '''
        一次一篇  
        計算fixation時duration留白  
        計算SR Research 抓取的gaze時, 填入duration
    '''
    result = []
    temp = []
    for i in text_box: # initail empty result
        for j in i:
            temp.append([0, j])
        result.append(temp)
        temp = []

    for s, t in enumerate(y):
        for r in range(1, len(rows)):
            if t < rows[r]: # match y, 直接對 "down"
                for c, box in enumerate(text_box[r-1]):
                    if x[s] < box[1]: # match x, 直接用 "right"
                        if duration == None:
                            result[r-1][c][0] += 1
                        else:
                            result[r-1][c][0] += duration[s]
                        break
                break
    return result # [time, (word)]


#_________________________________ SACCADE _________________________________

def word_back(rows, text_box, data): # calculate the accumulated gaze time
    '''
        一次一篇, 轉text, 再轉字典計算次數  
        計算[initial->final, times, cum_duration]
    '''
    x0, y0, x1, y1, duration = data

    axis2word = [[0]]*len(y0)
    # get raw data from ESAC
    for i in [[x0, y0], [x1, y1]]:
        x, y = i
        for s, t in enumerate(y):
            for r in range(1, len(rows)):
                if t < rows[r]: # match y, 直接對 "down"
                    for c, box in enumerate(text_box[r-1]):
                        if x[s] < box[1]: # match x, 直接用 "right"
                            axis2word[s] = axis2word[s] + [text_box[r-1][c][2]]
                            if axis2word[s][0] == 0: # 兩次應該相同, 只算一次
                                axis2word[s][0] = int(duration[s])
                            break
                    break
    word2dict = [[], []]
    # transfer form as initial->final, times, duration
    for back in axis2word:
        if len(back) == 3: # exclude points that fall ouside the article, may be a blinking(need check).
            combination = str(back[1][1])+"_"+str(back[1][0])+" > "+str(back[2][1])+"_"+str(back[2][0])
            counter = [1, back[0]]
            if combination in word2dict[0]: # 已存在
                p = word2dict[0].index(combination)
                word2dict[1][p][0] += 1
                word2dict[1][p][1] += back[0]
            else: # 新組合
                word2dict[0].append(combination)
                word2dict[1].append(counter)

    return word2dict # [ initial(No.)->final(No.), [times, sum of duration] ]


if __name__ == "__main__":
    print()




    




