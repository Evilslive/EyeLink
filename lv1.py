
import extractor as ex
import os
import matplotlib.pyplot as plt

def subject(path):
    data_list = [] # store subject data list, length for data
    f_list = os.listdir(path)
    for s, t in enumerate(f_list):
        if t[:3] == "twn" and t[-6:] == "en.asc":
            data_list.append(int(t[3:-6]))
        else:
            data_list.append(s) # make sure the files in the folder are the same exp.
    # or create your own subject number
    data_list.sort()
    
    print("The list of subject numbers from files as follows:","\n",data_list)
	
    return data_list

def write_fix_table(v_axis, h_axis, data, file_name): # 縱軸、橫軸、data
    with open(file_name+".txt", 'w') as w:
        w.write("字詞＼編號") # 寫下欄位名稱
        for h in h_axis:
            w.write("\tSubj.{:02d}".format(h))
        w.write("\n")

        for s, v in enumerate(v_axis):
            for i, j in enumerate(v):
                w.write(str(j)+"\t")
                w.write("\t".join("%s" %k for k in data[s][i])+"\n")

def write_sac_table(v_axis, h_axis, data, file_name):
    '''
        v_axis需組成一行, 同時移動h_axis
    '''
    combine_v = [[] for i in range(len(v_axis))]
    # 先處理一次 路徑
    for p, articles in enumerate(v_axis): #[篇章][受試者][跳視路徑]
        for subj in articles:
            for back in subj:
                if back not in combine_v[p]:
                    combine_v[p].append(back)
    # 再處理data
    for p in range(len(combine_v)): # 文章篇數
        for k in range(len(data[p])): # 受試者人數
            while len(data[p][k]) < len(combine_v[p]):
                data[p][k].append([]) # 對齊
    # match data to path
    for a, articles in enumerate(data):
        for s, subj in enumerate(articles):
            for b, back in enumerate(subj):
                if b >= len(v_axis[a][s]):
                    break
                k = combine_v[a].index(v_axis[a][s][b]) # 一定都在, 最後位置
                data[a][s][k], data[a][s][b] = data[a][s][b], data[a][s][k]

    with open(file_name+".txt", 'w') as w:
        w.write("起迄＼編號") # 寫下欄位名稱
        for h in h_axis:
            w.write("\tSubj.{:02d}".format(h))
        w.write("\n")
        
        for s, p in enumerate(combine_v):
            for i, j in enumerate(p):
                w.write(str(j)+"\t")
                for k in range(len(data[s])):
                    w.write(str(data[s][k][i])+"\t")
                w.write("\n")
            w.write("\n")

def lv1(subj_no, rows, text_box):
    '''
        get subject data one by one
    '''
    word_tb, gaze_tb = [[]], [[]]
    path_tb, saccade_tb = [[]], [[]] # [篇章][受試者]

    for no in subj_no: #data_list:
        print("Subj.No_{:02d}".format(no)+" processing...", end="\r")
        location, fixation, glance = ex.read_asc(path_asc+"twn{:02d}en.asc".format(no))
        pages = len(location)
        
        for p in range(pages):
            # calculate time of gaze, [time, (no, word)]
            gaze = ex.accumulate_fix_time(rows[p], text_box[p], fixation[p][0], fixation[p][1], fixation[p][2])
            # calculate saccade mode, [time, initial, final]
            saccade = ex.word_back(rows[p], text_box[p], glance[p])

            gaze_line = []
            # for fixation
            for i in gaze: # 段落組合
                for j in i:
                    gaze_line.append(j)

            if len(word_tb) < p+1: # add space of articles
                word_tb.append([])
                gaze_tb.append([])
            
            for s, t in enumerate(gaze_line):
                word = t[1][2]
                time = t[0]
                if subj_no.index(no) == 0: # word list once
                    word_tb[p].append(word)
                    gaze_tb[p].append([time])
                else:
                    gaze_tb[p][s].append(time)
            
            # for saccade
            if len(path_tb) < p+1:
                path_tb.append([])
                saccade_tb.append([])

            # [word, time]
            path_tb[p].append(saccade[0])
            saccade_tb[p].append(saccade[1])

        print("Subj.No_{:02d}".format(no)+" Completed !")

    write_fix_table(word_tb, subj_no, gaze_tb, "fixtion")
    write_sac_table(path_tb, subj_no, saccade_tb, "saccade")
    
    return word_tb, gaze_tb, saccade_tb


if __name__ == "__main__":

    path_asc = "The path where asc files"
    path_L2_ia = "The path where your L2 aoi files"
    path_L1_ia = "The path where your L1 aoi files"

    #_______________________
	# get subject file
    data_list = subject(path_asc)

    #_______________________
    # get AOI for current analysis
    rows, text_box = ex.road_IA(path_L2_ia)
   
    lv1(data_list, rows, text_box)


