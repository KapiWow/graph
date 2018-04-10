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

point = int(random.randrange(0, len(highwayNode)))
count = 0
for i in shops:
    if count < 10:
        shop = shops[i]
        paths.append(dijkstra_path(G, nodes[point], shop["highwayId"]))
        pathLen = dijkstra_path_length(G, nodes[point], shop["highwayId"])
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
print("--- %s seconds ---" % (time.time() - start_time))

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
print("--- %s seconds ---" % (time.time() - start_time))


def manhattan(a, b):
    w = float(allNodes[a]["w"])
    h = float(allNodes[a]["h"])
    w2 = float(allNodes[b]["w"])
    h2 = float(allNodes[b]["h"])
    return (math.fabs(w - w2)+math.fabs(h - h2))
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
print("--- %s seconds ---" % (time.time() - start_time))


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
print("--- %s seconds ---" % (time.time() - start_time))


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

print("--- %s seconds ---" % (time.time() - start_time))