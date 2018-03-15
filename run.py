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
for elem in root:
     if elem.tag == "node":
        point = {}
        point["h"] = elem.get("lat") 
        point["w"] = elem.get("lon") 
        allNodes[int(elem.get("id"))] = point

print(len(ways))
print(len(allNodes))

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
for i in deleteNode:
    highwayNode.pop(i)

print("count of nodes ",len(highwayNode))
#координаты всех линий для отрисовки карты
lines = []
#поиск всех line из дорог, которые связывают перекрестки
for point in ways:
    way = ways[point]
    a = 0
    while a < len(way["ref"]):
        if a != len(way["ref"])-1:
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
print("count of lines ", len(lines))

import csv
#записывает список смежности
def csv_dict(data, path):
    with open(path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for key in data:
            row = data[key]
            row.insert(0,key)
            writer.writerow(row)
            
path = "list.csv"
csv_dict(highwayNode, path)
#записывает матрицу смежности по списку смежности
def csv_matrix(path, ways):
    with open(path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for key in ways:
            row = []
            for item in ways:
                if item in ways[key]:
                    if item != key:
                        row.append(1)
                    else:
                        row.append(0)
                else:
                    row.append(0)
            writer.writerow(row)

path = "matrix.csv"
csv_matrix(path, highwayNode)


from Tkinter import Tk, Canvas, Frame, BOTH
#инициализирует окно и отрисовывает все линии
class Example(Frame):
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
#             print(line)
            canvas.create_line([line["x1"], line["y1"]], [line["x2"], line["y2"]])
        
        canvas.pack(fill=BOTH, expand=1)
root = Tk()
root.geometry("800x500+600+600")

ex = Example(root)
root.mainloop()  
