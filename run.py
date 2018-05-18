#!/usr/bin/python
# -*- coding: utf-8 -*-
from lxml import etree
#Считываем файл, подготовливаем его для обработки как xml
with open("map.xml") as fobj:
    xml = fobj.read()
root = etree.fromstring(xml)
#содержит все дороги, помеченные как highway
ways = {}
#Просматриваем все way, добавляем только те, у которых в tag есть highway,
#также добавляем им в ref все node, которые относятся к way
for obj in root:
    if obj.tag == "way":
        adeleteNode = False
        point = {}
        point["ref"] = [] 
        for tags in obj:
            if tags.tag == "tag":
                if tags.get("k") == "highway":
                    adeleteNode = True
            if tags.tag == "nd":
                point["ref"].append(tags.get("ref"))                 
        if adeleteNode:
            ways[int(obj.get("id"))] = point
#содержит все node, а также их координаты
allNodes = {}
#все магазины
shops = {}
for elem in root:
     if elem.tag == "node":
        point = {}
        point["h"] = elem.get("lat") 
        point["w"] = elem.get("lon") 
        allNodes[int(elem.get("id"))] = point
        for tags in elem:
            if tags.get("v") == "supermarket":
                shopID = int(elem.get("id"))
                shops[shopID] = {}
                shops[shopID]["point"] = point
                shops[shopID]["r"] = 1.0
                    

#все Node, которые лежат на highway
highwayNode = {}
#количество дорог, в которые входит node
roadCount = {}
#ищем roadCount, highwayNode
for point in ways:
    way = ways[point]
    for a in range(0, len(way["ref"])):
        node = int(way["ref"][int(a)])
        if node in roadCount:
            roadCount[node] = roadCount[node] + 1
        else:
            roadCount[node] = 1
        if node not in highwayNode:
            highwayNode[node] = []
        if a!= 0:
            highwayNode[node].append(int(way["ref"][int(a-1)]))
        if a!= len(way["ref"])-1:
            highwayNode[node].append(int(way["ref"][int(a+1)]))
#node, которые не являются перекрестками
deleteNode = []
# Если node имеет 2 соседа и состоит только 1 дороге, то это не перекресток, удаляем его
for i in highwayNode:
    if len(highwayNode[i]) == 2:
        if (roadCount[i] == 1):
            deleteNode.append(i)
            #соединяем оставшиеся вершины в дороге
            highwayNode[highwayNode[i][1]].append(highwayNode[i][0])
            highwayNode[highwayNode[i][0]].append(highwayNode[i][1])
            highwayNode[highwayNode[i][0]].remove(i)
            highwayNode[highwayNode[i][1]].remove(i)

for i in deleteNode:
    highwayNode.pop(i)

#start deleting nodes

import math
from networkx import *
G = nx.Graph()
# используем библиотеку networkx, записываем туда данные наших ребер
for i in highwayNode:
    for j in highwayNode[i]:
        w = float(allNodes[i]["w"])
        h = float(allNodes[i]["h"])
        w2 = float(allNodes[j]["w"])
        h2 = float(allNodes[j]["h"])
        G.add_edge(i, j, weight = ((w-w2)**2+(h-h2)**2)**0.5)
#выделяем компоненты связности
graphs = list(nx.connected_component_subgraphs(G))
#выбираем самую большую, это и есть наш город
maxx = 0
maxI = graphs[0]
for i in graphs:
    if maxx <i.number_of_nodes():
        maxx = i.number_of_nodes()
        maxI = i
#удаляем все узлы из других компонент
deleteNode = []
for i in highwayNode:
    if i not in maxI.nodes:
        deleteNode.append(i)

for i in deleteNode:
    highwayNode.pop(i)

#end deleting nodes

write_adjlist(maxI,"test.adjlist")
#находим ближайший узел к магазину
for i in highwayNode: 
    for shop in shops:
        hShop = float(shops[shop]["point"]["h"])
        wShop = float(shops[shop]["point"]["w"])
        h = float(allNodes[i]["h"])
        w = float(allNodes[i]["w"])
        if ((h - hShop)*(h - hShop)+(w - wShop)*(w - wShop)) < shops[shop]["r"]:
            shops[shop]["highwayId"] = i
            shops[shop]["r"] = ((h - hShop)*(h - hShop)+(w - wShop)*(w - wShop))

#координаты всех линий для отрисовки карты
lines = []
#поиск всех line из дорог, которые связывают перекрестки
for point in ways:
    way = ways[point]
    a = 0
    while a < len(way["ref"]):
        if (a != len(way["ref"])-1)and(int(way["ref"][int(a)])  in highwayNode):
            line = {}
            resize = 5000
            step = 1
            while (int(way["ref"][int(a+step)]) not in highwayNode) and (a+step<len(way["ref"])-1):
                step = step + 1
            currentNode = allNodes[int(way["ref"][int(a)])]
            nextNode = allNodes[int(way["ref"][int(a+step)])]
            left = 44.7240
            bottom = 48.7435
            line["y1"] = 500-int((float(currentNode["h"])-bottom)*resize)
            line["x1"] = int((float(currentNode["w"])-left)*resize)
            line["y2"] = 500-int((float(nextNode["h"])-bottom)*resize)
            line["x2"] = int((float(nextNode["w"])-left)*resize)
            lines.append(line)
            a = a + step - 1
        a = a + 1
#поиск кратчайшего пути и ближайшего магазина
nodes = list(maxI.nodes)
paths = []
minPath = 10000
minPathId = 0
import random

def manhattan(a, b):
    w = float(allNodes[a]["w"])
    h = float(allNodes[a]["h"])
    w2 = float(allNodes[b]["w"])
    h2 = float(allNodes[b]["h"])
    return (math.fabs(w - w2)+math.fabs(h - h2))

point = int(random.randrange(0, len(highwayNode)))
count = 0
for i in shops:
    if count < 10:
        shop = shops[i]
        # astar_path(G, nodes[point], shop["highwayId"], manhattan)
        paths.append(astar_path(G, nodes[point], shop["highwayId"], manhattan))
        pathLen = astar_path_length(G, nodes[point], shop["highwayId"], manhattan)
        # paths.append(dijkstra_path(G, nodes[point], shop["highwayId"]))
        # pathLen = dijkstra_path_length(G, nodes[point], shop["highwayId"])
        print(pathLen*3*60)
        if pathLen < minPath:
            minPath = pathLen
            minPathId = count
    count = count + 1
print minPathId

from Tkinter import Tk, Canvas, Frame, BOTH
#отрисовка всей карты и выделение путей до магазинов 
class pathDraw(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)   
        self.parent = parent        
        self.initUI()
        
    def initUI(self):
        self.parent.title("Lines")        
        self.pack(fill=BOTH, expand=1)

        canvas = Canvas(self)        
        for a in range(0,len(lines)):
            line = lines[a]
            canvas.create_line([line["x1"], line["y1"]], [line["x2"], line["y2"]])
            
        count = 0
        for path in paths:
            for a in range(0,len(path)-1):
                line = {}
                resize = 5000
                currentNode = allNodes[path[a]]
                nextNode = allNodes[path[a+1]]
                left = 44.7240
                bottom = 48.7435
                line["y1"] = 500-int((float(currentNode["h"])-bottom)*resize)
                line["x1"] = int((float(currentNode["w"])-left)*resize)
                line["y2"] = 500-int((float(nextNode["h"])-bottom)*resize)
                line["x2"] = int((float(nextNode["w"])-left)*resize)
                if count == minPathId:
                    canvas.create_line([line["x1"], line["y1"]], [line["x2"], line["y2"]],fill="red",width = 4)
                else:
                    canvas.create_line([line["x1"], line["y1"]], [line["x2"], line["y2"]],fill="blue",width = 1)
            count = count + 1
        
        canvas.pack(fill=BOTH, expand=1)

root3= Tk()
root3.geometry("800x500+600+600")
ex3= pathDraw(root3)
root3.mainloop()  

import time
start_time = time.time()
for a in range(0,10):   
    count = 0
    point = int(random.randrange(0, len(highwayNode)))
    for i in shops:
        if count < 10:
            shop = shops[i]
            pathLen = dijkstra_path(G, nodes[point], shop["highwayId"])
        count = count + 1
print("dijkstra_path --- %s seconds ---" % (time.time() - start_time))

def Euc(a, b):
    w = float(allNodes[a]["w"])
    h = float(allNodes[a]["h"])
    w2 = float(allNodes[b]["w"])
    h2 = float(allNodes[b]["h"])
    return ((w - w2) ** 2 + (h - h2) ** 2) ** 0.5
import time
start_time = time.time()
for a in range(0,10):   
    count = 0
    point = int(random.randrange(0, len(highwayNode)))
    for i in shops:
        if count < 10:
            shop = shops[i]
            pathLen = nx.astar_path(G, nodes[point], shop["highwayId"], Euc)
        count = count + 1
print("astar_path Euc--- %s seconds ---" % (time.time() - start_time))


import time
start_time = time.time()
for a in range(0,10):   
    count = 0
    point = int(random.randrange(0, len(highwayNode)))
    for i in shops:
        if count < 10:
            shop = shops[i]
            pathLen = nx.astar_path(G, nodes[point], shop["highwayId"], manhattan)
        count = count + 1
print("astar_path manhattan--- %s seconds ---" % (time.time() - start_time))


def cheb(a, b):
    w = float(allNodes[a]["w"])
    h = float(allNodes[a]["h"])
    w2 = float(allNodes[b]["w"])
    h2 = float(allNodes[b]["h"])
    return max(math.fabs(w - w2), math.fabs(h - h2))
import time
start_time = time.time()
for a in range(0,10):   
    count = 0
    point = int(random.randrange(0, len(highwayNode)))
    for i in shops:
        if count < 10:
            shop = shops[i]
            pathLen = nx.astar_path(G, nodes[point], shop["highwayId"], cheb)
        count = count + 1
print("astar_path cheb--- %s seconds ---" % (time.time() - start_time))


start_time = time.time()
for a in range(0,10):
    d = {}
    m2={}
    m1=[]
    m11=[]
    m0={}
    for i in nodes:
        d[i]=10000
        m2[i]=True
        m0[i]=False
    point = int(random.randrange(0, len(highwayNode)))
    d[nodes[point]]=0
    m2[nodes[point]] = False
    m1.append(nodes[point])
    while (len(m1)>0)or(len(m11)>0):
        if len(m11)>0:
            u = m11.pop()
        else:
            u = m1.pop()
        for v in G.neighbors(u):
            if m2[v]:
                m2[v]=False
                m1.append(v)
                d[v]=min(d[v],d[u]+ G[u][v]['weight'])
            elif v in m1:
                d[v]=min(d[v],d[u]+ G[u][v]['weight'])
            elif (m0[v])and(d[v]>d[u]+ G[u][v]['weight']):
                d[v]=G[u][v]['weight']
                m11.append(v)
                m0[v]=False
            m0[u]=True
    count = 0
    for i in shops:
        if count < 10:
            shop = shops[i]
        count = count + 1

print("astar_path Levith--- %s seconds ---" % (time.time() - start_time))




# print(shops[1236954369])

import time
start_time = time.time()

G2 = nx.Graph()
# for i in range(0,10):
#     G2.add_vertex()
#     for j in highwayNode[i]:
#         w = float(allNodes[i]["w"])
#         h = float(allNodes[i]["h"])
#         w2 = float(allNodes[j]["w"])
#         h2 = float(allNodes[j]["h"])
#         G.add_edge(i, j, weight = math.sqrt((w-w2)*(w-w2)+(h-h2)*(h-h2)))
      
count = 0
ddel = []
for i in shops:
    if count >= 10:
        ddel.append(i)
    count = count + 1
for i in ddel:
    shops.pop(i)
    
# print(shops)
left = []
for i in shops:
    left.append(shops[i]["highwayId"])
    count = 0
    shop1 = shops[i]
#     point = int(random.randrange(0, len(highwayNode)))
    for j in shops:
        shop2 = shops[j]
#             pathLen = dijkstra_path(G, nodes[point], shop["highwayId"])
        pathLen = nx.astar_path_length(G, shop1["highwayId"], shop2["highwayId"], manhattan)
#             print(dijkstra_path_length(G, nodes[point], shop["highwayId"]))
#         print(pathLen)
        G2.add_edge(shop1["highwayId"], shop2["highwayId"], weight = pathLen)
    count = count + 1
#     print(a)
print("--- %s seconds ---" % (time.time() - start_time))

import copy
path = []
path.append(left[0])
pathLen = 0
# print(list(G2.nodes))
leafs = []
leaf = {}
leaf['matrix'] = []
count = 0
maxInt = 1000000000


leaf['strMin'] = range(0,10)
leaf['colMin'] = range(0,10)
kk = []
for i in list(G2.nodes):
    leaf['matrix'].append([])
    for j in list(G2.nodes):
        leaf['matrix'][count].append(int(10000*G2[i][j]['weight']))
    leaf['matrix'][count][count] = maxInt
    count = count + 1

for i in leaf['matrix']:
    print(i)
S = 0

kk = copy.deepcopy(leaf['matrix'])

for i in range(0,len(list(G2.nodes))):
    minV = leaf['matrix'][0][i]
    for j in range(1,len(list(G2.nodes))):
        minV = min(minV,leaf['matrix'][j][i])
    for j in range(0,len(list(G2.nodes))):        
        leaf['matrix'][j][i] = leaf['matrix'][j][i] - minV
#     leaf['colMin'][i] = minV
    S = S + minV
for i in range(0,len(list(G2.nodes))):
    minV = leaf['matrix'][i][0]
    for j in range(1,len(list(G2.nodes))):
        minV = min(minV,leaf['matrix'][i][j])
    for j in range(0,len(list(G2.nodes))):        
        leaf['matrix'][i][j] = leaf['matrix'][i][j] - minV
#     leaf['strMin'][i] = minV
    S = S + minV   
    
# for i in range(0,len(list(G2.nodes))):
#     minV = leaf['matrix'][0][i]
#     for j in range(1,len(list(G2.nodes))):
#         if leaf['matrix'][j][i]>0:
#             minV = min(minV,leaf['matrix'][j][i])
#     leaf['colMin'][i] = minV
path2 = []
nn=[]

leaf = {}
leaf['matrix'] = []
count = 0
maxInt = 1000000000


leaf['strMin'] = range(0,10)
leaf['colMin'] = range(0,10)
kk = []
for i in list(G2.nodes):
    leaf['matrix'].append([])
    for j in list(G2.nodes):
        leaf['matrix'][count].append(int(10000*G2[i][j]['weight']))
    leaf['matrix'][count][count] = maxInt
    count = count + 1

# for i in leaf['matrix']:
#     print(i)
S = 0

kk = copy.deepcopy(leaf['matrix'])
kk2 = copy.deepcopy(kk)


for k in range(0,9):
    # print(nn)
    mm = maxInt
    xx = 0
    yy = 0
#     print(k)
#     for i in kk2:
#         print(i)
    for i in range(0,10):
        for j in range(0,10):
            if kk2[i][j]<mm:
                mm = kk2[i][j]
                xx = i
                yy = j
    if len(nn) == 0:
        nn.append([])
        nn[0].append(xx)
        nn[0].append(yy)
    else:
        ff = False
        xxx = []
        yyy = []
        for aa in nn:
            if xx in aa:
                ff = True
                xxx = aa
            if yy in aa:
                yyy = aa
                ff = True
        
        if len(xxx)>0 and len(yyy)>0:
            for pp in xxx:
                yyy.append(pp)
            nn.remove(xxx)
        else:    
            if ff:
                if len(xxx)>0:
                    xxx.append(yy)
                if len(yyy)>0:
                    yyy.append(xx)         
#             if xx in aa or yy in aa:
#                 ff = True
#                 if not(yy in aa):
#                     aa.append(yy)
#                 if not(xx in aa):
#                     aa.append(xx)
                
        if not(ff):
            nn.append([xx,yy])
#         if not(yy in nn):
#             nn.append(yy)
    path2.append([xx,yy])
    for aa in range(0,10):
        kk2[xx][aa] = maxInt
    for aa in range(0,10):
        kk2[aa][yy] = maxInt
    for aa in nn:
        for i in aa:
            for j in aa:
                kk2[i][j]=maxInt
print("path2") 

strI = range(0,10)
colI = range(0,10)

for i in path2:
    strI.remove(i[0])
    colI.remove(i[1])

path2.append([strI[0],colI[0]])
print(path2)

Sum = 0
for i in path2:
    Sum += kk[i[0]][i[1]]
print(Sum)

path = []
path.append(left[0])
pathLen = 0
# print(list(G2.nodes))
print(left)
for i in range(0,9):
    minPath = G2[left[0]][path[-1]]['weight']
    node = left[0]
    for j in left:
        if G2[j][path[-1]]['weight'] < minPath:
            minPath = G2[j][path[-1]]['weight']
            node = j
    pathLen = pathLen + minPath
    path.append(node)
    left.remove(node)
pathLen = pathLen + G2[path[0]][path[-1]]['weight']
print(path)
print(int(pathLen*10000))


class pathDraw(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)   
        self.parent = parent        
        self.initUI()
        
    def initUI(self):
        self.parent.title("Lines")        
        self.pack(fill=BOTH, expand=1)

        canvas = Canvas(self)        
        for a in range(0,len(lines)):
            line = lines[a]
            canvas.create_line([line["x1"], line["y1"]], [line["x2"], line["y2"]])
            
        count = 1
        for i in range(0,10):
            pathh = nx.dijkstra_path(G, path[i-1], path[i])
            for a in range(0,len(pathh)-1):
                line = {}
                resize = 5000
                currentNode = allNodes[pathh[a]]
                nextNode = allNodes[pathh[a+1]]
                left = 44.7240
                bottom = 48.7435
                line["y1"] = 500-int((float(currentNode["h"])-bottom)*resize)
                line["x1"] = int((float(currentNode["w"])-left)*resize)
                line["y2"] = 500-int((float(nextNode["h"])-bottom)*resize)
                line["x2"] = int((float(nextNode["w"])-left)*resize)
                canvas.create_line([line["x1"], line["y1"]], [line["x2"], line["y2"]],fill="red",width = count)
            count = count + 1
        
        canvas.pack(fill=BOTH, expand=1)
root4= Tk()
root4.geometry("800x500+600+600")

ex4= pathDraw(root4)

root4.mainloop()  