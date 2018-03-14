from lxml import etree

points = {}

count = 0;    
with open("map.xml") as fobj:
    xml = fobj.read()

root = etree.fromstring(xml)

for obj in root:
    if obj.tag == "way":
        add = False;
        point = {}
        point["ref"] = [] 
        for tags in obj:
            if tags.tag == "tag":
                if tags.get("k") == "highway":
                    add = True;
            if tags.tag == "nd":
                point["ref"].append(tags.get("ref"))
                        
        if add:
            points[int(obj.get("id"))] = point
                    
allNodes = {}
for elem in root:
     if elem.tag == "node":
        point = {}
        point["h"] = elem.get("lat") 
        point["w"] = elem.get("lon") 
        allNodes[int(elem.get("id"))] = point
count = 0;    
print(len(points))
print(len(allNodes))
    
highPoint = {}
highPoint2 = {}

print("count")
lines = []
for point in points:
    pp = points[point]
    for a in range(0, len(pp["ref"])):
        if int(pp["ref"][int(a)]) in highPoint2:
            highPoint2[int(pp["ref"][int(a)])] = highPoint2[int(pp["ref"][int(a)])] + 1
        else:
            highPoint2[int(pp["ref"][int(a)])] = 1
        if int(pp["ref"][int(a)]) not in highPoint:
            highPoint[int(pp["ref"][int(a)])] = []
        if a!= 0:
            highPoint[int(pp["ref"][int(a)])].append(int(pp["ref"][int(a-1)]))
        if a!= len(pp["ref"])-1:
            highPoint[int(pp["ref"][int(a)])].append(int(pp["ref"][int(a+1)]))
count = 0
dd = []
print(len(highPoint))

for i in highPoint:
    if len(highPoint[i]) == 2:
        if (highPoint2[i] == 1):
            dd.append(i)
for i in dd:
    highPoint.pop(i)
    
for i in highPoint:
    count = count + 1

print(len(highPoint))

print(len(lines))

for point in points:
    pp = points[point]
    a = 0
    while a < len(pp["ref"]):
        if a != len(pp["ref"])-1:
            line = {}
            ff = 5
            step = 1
            while (int(pp["ref"][int(a+step)]) not in highPoint) and (a+step<len(pp["ref"])-1):
                step = step + 1
            
            line["y1"] = 500-int((float(allNodes[int(pp["ref"][int(a)])]["h"])-48.7435)*1000*ff)
            line["x1"] = int((float(allNodes[int(pp["ref"][int(a)])]["w"])-44.7240)*1000*ff)
            line["y2"] = 500-int((float(allNodes[int(pp["ref"][int(a+step)])]["h"])-48.7435)*1000*ff)
            line["x2"] = int((float(allNodes[int(pp["ref"][int(a+step)])]["w"])-44.7240)*1000*ff)
            lines.append(line)
            a = a + step - 1
        a = a + 1
print(len(lines))

import csv
def csv_dict(data, path):
    with open(path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for key in data:
            row = data[key]
            row.insert(0,key)
            writer.writerow(row)
            
path = "output.csv"
csv_dict(highPoint, path)
path = "matrix.csv"

def csv_matrix(path, points):
    with open(path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for key in points:
            row = []
            for item in points:
                if item in points[key]:
                    if item != key:
                        row.append(1)
                    else:
                        row.append(0)
                else:
                    row.append(0)
            writer.writerow(row)


csv_matrix(path, highPoint)

from Tkinter import Tk, Canvas, Frame, BOTH

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