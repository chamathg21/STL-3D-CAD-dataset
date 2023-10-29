import numpy as np
import trimesh
import os
import sys
from check import check
import gc 
import argparse
import git
import time
import datetime 

times = []

def run(args,filepath,filename,report,d,failed,f):
    d+=1
    report.append('')
    start_time = time.time()
    #t = datetime.timedelta(seconds=time.time())
    # get total seconds?
    report,d,failed = check(args,filepath,filename,report,d,failed)
    print(report[d],file=f)
    gc.collect()
    #t.seconds-=time.time()
    #times.append(t.total_seconds())
    times.append((time.time()-start_time))
    return d

parser = argparse.ArgumentParser(prog="analysis.py",
                                 description="Detects if voids are present in given STL files",
                                 )
group = parser.add_mutually_exclusive_group()
group.add_argument('-d','--directory',help="specify directory to analyze",action='store_true')
group.add_argument('-f','--file',help="specify file to analyze",action='store_true')
parser.add_argument('filenameOrPath',action='store')
parser.add_argument('-i','--info',help="provide amount of void in each shell (longer report)",action='store_true')
args = parser.parse_args()

if args.directory:
    filepath = args.filenameOrPath
if args.file:
    filename = args.filenameOrPath

# setup report string
if args.info:
    report = ['file,num_shells,shell_num,shell_amt_void,enclosures,has_hidden_void,void_num,center_mass,bounds']
elif not args.info:
    report = ['file,has_hidden_void,void_num,center_mass,bounds,Risk Factor'] 
failed=[]
# d for design number
vf=input('running on v or f data set? ')
lim = int(input('please provide input limit for data set: '))
while lim<0 or type(lim)!=int or vf not in ['v','f','V','F']:
    vf=input('running on v or f data set? ')
    lim = int(input('please provide input limit for data set: '))

d=0
f=open(f'report_{vf}_{lim}.csv','w')
print(report[d],file=f)
if args.directory:
 #   if filepath=='STL-3D-CAD-dataset':
        # https://stackoverflow.com/a/15315667
  #      g = git.cmd.Git(filepath)
   #     g.pull()
    # https://stackoverflow.com/a/53432676
    for filename in os.listdir(filepath):
        if filename.lower().endswith('.stl'): # .lower() because .STL is possible
            d=run(args,filepath,filename,report,d,failed,f)
            print("done")

if args.file:
    d=run(args,None,filename,report,d,failed,f)
    print("done")

f.close()
t=open(f'times_{vf}_{lim}.csv','w')
for time in times:
    print(str(time),file=t)
t.close()
