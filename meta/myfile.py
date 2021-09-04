import os

path = 'd:\\College 2\\Q2\\2IMV20 Visualization\\Visualization-Assignments\\Assignment 1\\meta\\structure_unionizes'
files = []
# r=root, d=directories, f = files
for r, d, f in os.walk(path):
    for file in f:
        print(file)


