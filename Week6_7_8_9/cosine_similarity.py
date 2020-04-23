#_*_coding:utf-8_*_
import pandas as pd
import numpy as np
import jieba
import math
from sklearn.preprocessing import MinMaxScaler


def extract_words_list(text_data):
    '''
    用jieba 的方法进行中文分词
    python使用jieba实现中文文档分词和去停用词，无用词等
    https://www.cnblogs.com/zuixime0515/p/9221156.html
    @param text_data: 初始的文本数据
    @return: 关键词
    '''
    # 1 对初始数据进行清洗
    if text_data == np.nan:
        text_data = ''
    text_data = text_data.replace('\\n', '').replace('\\t', '').replace('\\xa0', '').replace('\\r', '')\
        .replace('\n', '').replace('\t', '').replace('\r', '').replace('\xa0', '')
    # 2 jieba 中文分词, 并全景模式
    words = jieba.cut(text_data, cut_all=True)
    # 3 对分好的词进行处理，
    # 3.1 导入 停用词库
    stop_words_dic = open('./stop_words.txt', 'rb')
    stop_words_list = stop_words_dic.read().splitlines()
    stop_words_dic.close()
    # 3.2 去掉空值，去掉单字，去掉数字，去掉停用词
    words = [x for x in words if
             ((x != '') and (len(x) > 1) and (not (str(x).isdigit())) and (not (x in stop_words_list)))]
    split_words = [w for w in words]
    return split_words


def calculate_similarity(text1, text2):
    '''计算两个文本余弦相似度
    http://www.luyixian.cn/news_show_256402.aspx
    计算两个文本的相似度，构建一个文本集合，计算词频，再计算相似度
    @param text1:
    @param text2:
    @return: 两个文本的余弦相似度
    '''
    # 1 分词
    words_list1 = extract_words_list(text1)
    words_list2 = extract_words_list(text2)
    # 2 列出所有的词，并组成一个集合
    words_dict = set(words_list1 + words_list2)
    # 3计算词频
    word_count1, word_count2 = {}, {}
    # 4写出词频向量
    word_count_vector1, word_count_vector2 = [], []
    # 5 对于词汇集合中的每一个词，统计他在原文本中出现的次数：没有就是0，有则 +1
    for word in words_dict:
        # 5.1 对文本中出现同样的词进行计数
        n1 = text1.count(word)
        n2 = text2.count(word)
        # 5.2 特殊处理：如果两个文本中都出现了相同的某个词，权重乘 1.5
        if (word in text1) and (word in text2):
            n1 *= 1.5
            n2 *= 1.5
        # 5.3 以 word 为键，以word出现的次数为值， 来构建键值对
        word_count1[word] = n1
        word_count2[word] = n2
        # 5.4 把词频一个个的添加到词频向量中，作为维度
        # [1,0,9,2,5,3,2,1,0,0,0,0,1,1,1]
        # [1,1,5,0,1,0,0,1,1,6,1,0,1,0,0]
        word_count_vector1.append(n1)
        word_count_vector2.append(n2)
    # # 使用标准化来把数据进行压缩到0, 1的区间 -> 无用的操作，因为向量缩放，夹角余弦值不变
    # scaler = MinMaxScaler()
    # vec1 = np.array(word_count_vector1).reshape(-1, 1)
    # vec2 = np.array(word_count_vector2).reshape(-1, 1)
    # vec1 = scaler.fit_transform(vec1)
    # vec2 = scaler.fit_transform(vec2)
    # 6 计算余弦相似度: 先把列表转化为 numpy的数组
    vec1 = np.array(word_count_vector1)
    vec2 = np.array(word_count_vector2)
    similar = cosine_distance(vec1, vec2)

    # print(similar)
    return similar


def cosine_distance(vector1, vector2):
    '''
    计算两个向量的夹角的余弦值
    @param vector1:
    @param vector2:
    @return:
    '''
    # 1 长度不相等，直接返回
    if len(vector1) != len(vector2):
        return None
    part_up = 0.0
    a_sq = 0.0
    b_sq = 0.0
    # 2 向量点积公式，
    # 上半部分是向量点积: x 点乘 y = x1y1 + x2y2 + x3y3
    # 下半部分是 向量模长的乘积结果再开根号 ||x||^2 = x1^2 + x2^2 + x3^2
    for a1, b1 in zip(vector1, vector2):
        # 2.1 上半部分就是向量各元素的对应乘积的 和
        part_up += a1 * b1
        a_sq += a1 ** 2
        b_sq += b1 ** 2
    part_down = math.sqrt(a_sq * b_sq)
    # 2.2 如果分母为0了，说明至少有一个是零向量，不可能发生，直接返回
    if part_down == 0.0:
        return None
    else:
        return part_up / part_down


def get_recommended_list(job_index, topN=10):
    '''
    在数据库中选择指定的岗位数据，针对岗位数据推荐出最匹配的推荐课程列表
    @return: 针对此课程的推荐列表
    @param job_index: 岗位的索引号
    @param topN: 想接受推荐的课程数量，默认为10
    @return:
    '''
    # 1 获取内容
    jobs_data = pd.read_csv('./Jobs_Courses_Datas/jobs_data.csv')
    courses_data = pd.read_csv('./Jobs_Courses_Datas/courses_data.csv')
    # 1.1 去掉有 NAN的行，并重设索引
    jobs_data = jobs_data.dropna().reset_index(drop=True)
    courses_data = courses_data.dropna().reset_index(drop=True)
    # 1.2 取出 job_index 对应的job信息
    job = jobs_data.iloc[job_index]
    job_title = job['job_title']
    job_describe = job['job_responsibility']
    # 1.3 把名字和描述都加进去参与匹配，但是名字的权重要再增加一点
    job_total = job_title * 2 + job_describe
    # courses_data = courses_data.iloc[198:202]
    # print(courses_data.iloc[199])
    # 2 构建一个列表存储：课程-岗位相似度，以及课程信息
    r_new = []
    for i in range(len(courses_data)):
        c = courses_data.loc[i]
        # 2.1 构建一个小字典存储：课程名字，课程描述，课程-岗位相似度
        r_t = c
        r_t['Recommended_Course_Name'] = c[0]
        r_t['Course_Description'] = c[1]
        r_t_total = r_t['Recommended_Course_Name'] * 2 + r_t['Course_Description']
        # 2.2 对 job名字，描述 和 课程名字，描述都进行匹配
        cos_similar = calculate_similarity(job_total, r_t_total)
        r_t['Job_Course_Similarity'] = cos_similar
        # 2.3 把生成的字典添加到列表中取
        r_new.append(r_t)
    # 2.3 对获得的列表按相似度为键，从高到低进行排序
    r_new = sorted(r_new, key=lambda z: z['Job_Course_Similarity'], reverse=True)
    r_new = pd.DataFrame(r_new)
    # 3 选取topN 课程： -> 用花式索引来获取，并打印
    # 3.1 先打印一下工作岗位的相关信息
    print('对于工作：%s，岗位描述信息如下：\n%s' % (job_title, job_describe))
    recommended_courses_list = r_new[['Recommended_Course_Name', 'Job_Course_Similarity']][:topN]
    print('对于工作：%s， 我们推荐学习的课程清单如下：\n %s' % (job_title, recommended_courses_list))
    return None


if __name__=='__main__':
    get_recommended_list(job_index=3278)

