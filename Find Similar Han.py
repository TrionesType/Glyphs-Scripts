#MenuTitle: Find Similar Han
# -*- coding: utf-8 -*-
from GlyphsApp import *
import os
import pickle

# 设置要显示的相似字符数量
K_SIMILAR_CHARS = 10

__vector_data = pickle.load(open(os.path.join(os.path.dirname(__file__), 'Find Similar Han.pkl'), 'rb'))

def get_vector(char):
    """
    获取字符的向量数据
    :param char: 字符
    :return: 向量数据
    """
    hex_string = '%04X' % ord(char)
    if hex_string in __vector_data:
        return __vector_data[hex_string]
    else:
        return None

def has_vector(char):
    """
    检查字符是否有向量数据
    :param char: 字符
    :return: 是否有向量数据
    """
    hex_string = '%04X' % ord(char)
    return hex_string in __vector_data

def distance_between_vectors(vec1, vec2):
    """
    计算两个向量之间的余弦距离
    :param vec1: 向量1
    :param vec2: 向量2
    :return:的余弦距离
    """
    if vec1 is None or vec2 is None:
        return float('inf')
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
    magnitude2 = sum(b ** 2 for b in vec2) ** 0.5
    if magnitude1 == 0 or magnitude2 == 0:
        return float('inf')
    return 1 - dot_product / (magnitude1 * magnitude2)

def similarity_score(char1, char2):
    """
    计算两个字符之间的相似度分数，越低越像
    :param char1: 字符1
    :param char2: 字符2
    :return: 相似度分数
    """
    vec1 = get_vector(char1)
    vec2 = get_vector(char2)
    return distance_between_vectors(vec1, vec2)

def __find_similar():
    current_char = Glyphs.font.selectedLayers[0].parent.string
    if not current_char or not has_vector(current_char):
        return
    available_chars = [ g.string for g in Glyphs.font.glyphs if g.export and g.string and has_vector(g.string)  ]
    # Sort the available characters by their similarity score to the current character
    available_chars.sort(key=lambda char: similarity_score(current_char, char))

    current_tab = Font.currentTab
    k_chars = min(K_SIMILAR_CHARS, len(available_chars))
    
    if current_tab:
        cursor = current_tab.textCursor
        current_tab.string = current_tab.string[:cursor+1] \
            + '\n' \
            + ''.join(available_chars[:k_chars])\
            + '\n' \
            + current_tab.string[cursor+1:]
    else:
        Font.newTab(current_char + '\n' + ''.join(available_chars[:K_SIMILAR_CHARS]))

__find_similar()