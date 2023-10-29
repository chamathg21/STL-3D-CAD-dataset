import csv
import argparse
import numpy as np
def precision(tp,fp):
    if tp+fp == 0:
        return "n/a"
    return tp/(tp+fp)
def recall(tp,fn):
    if (tp+fn)==0:
        return "n/a"
    return tp/(tp+fn)
def accuracy(tp,tn,fp,fn):
    if tp+tn+fp+fn == 0:
        return "n/a"
    return (tp+tn)/(tp+tn+fp+fn)
def f1(tp,fp,fn):
    #f1 = 2* (precision * recall)/(precision + recall)
    p = precision(tp,fp)
    r = recall(tp,fn)
    if  p=='n/a' or r=='n/a' or p+r==0:
        return 'n/a'
    return 2*((p*r)/(p+r))

def array1d_match(r,o):
    o = [round(x,3) for x in o ]
    assert len(r)==len(o),'lists not same length'
    eq = True
    for i in range(len(r)):
        if abs(r[i] - o[i]) > 0.002:
            eq = False
    #print(f'{r}=={o}? {eq}')
    return eq

def array2d_match(r,o):
    o = [[round(x,3) for x in lst] for lst in o]
    assert len(r)==len(o) and len(r[0])==len(o[0]) and len(r[1])==len(o[1]),'lists not same length'
    eq = True
    for i in range(len(r)):
        for j in range(len(r[i])):
            if abs(r[i][j] - o[i][j])>0.002:
                eq = False
            #print(f'{r[i][j]}=={o[i][j]}? {r[i][j]==o[i][j]}')
    #print(f'{r}=={o}? {eq}')
    return eq


def compare(e,eo):
    # need to make sure center_mass and bounds match
    ceq = False
    beq = False
    ceq = array1d_match(e[2],eo[1])
    beq = array2d_match(e[3],eo[2])
    return ceq and beq

parser = argparse.ArgumentParser(prog="eval.py",
                                 description="Computes evaluation metrics for analysis and oracle reports.",
                                 )
parser.add_argument('-a','--analysis',help="specify analysis report",action='store_true',required=False)
parser.add_argument('a_report',action='store')
parser.add_argument('-o','--oracle',help="specify oracle report",action='store_true',required=False)
parser.add_argument('o_report',action='store')
args = parser.parse_args()



# get both csv files 
oraclef = open(args.o_report,'r')
reportf = open(args.a_report,'r')



# put each line as a dictionary.
# report[filename] = (has_hidden_void,void_num,center_mass,bounds)
# or... report[filename] = [(has,...),(has...),...]
# if there's no voids then maybe  ('NO',None,None,None) ?
# oracle[filename] =  (void number,center mass,bounds)

report = dict()
oracle = dict()
err = []

reportf.readline()
reader_r = csv.reader(reportf)
for row in reader_r:
    if 'Error' in row[1] or 'error' in row[1]:
        err.append(row[0])
        continue
    # remove '_void.stl' characters  
    row[0] = row[0][0:-9]
    if row[3] and row[4]:
        cm = eval(row[3])
        bd = eval(row[4].strip('\n'))
    else:
        cm = row[3]
        bd = row[4]
    if row[0] in report:
        report[row[0]].append((row[1],row[2],cm,bd))
    else:
        report[row[0]]=[(row[1],row[2],cm,bd)]

    #print(report[line[0]])

#oraclef.readline()
readero = csv.reader(oraclef)
for row in readero:
    #print(row[0])
    #row[0] = row[0].strip("\\")
    #if '\\' == row[0][0]:
    #    row[0]= row[0][1:]
    #print(row[0])
    #print(len(row))
    #print('stripped row:',row.strip('\n\"'))
    cm = eval(row[2])
    bd = eval(row[3].strip('\n'))

    if row[0] in oracle:
        oracle[row[0]].append((row[1],cm,bd))
    else:
        oracle[row[0]]=[(row[1],cm,bd)]
    #print(oracle[line[0]])

tp = 0
fp = 0
tn = 0
fn = 0

#r = 0
#for f in report:
#    r+=len(report[f])
#    for i in report[f]:
#        print(f,i[1])
#print(f'number of report records: {r}')
#o = 0
#for f in oracle:
#    o+=len(oracle[f])
#    for i in oracle[f]:
#        print(f,i[0])
#print(f'number of oracle records: {o}')
#print(oracle)
#
#
# if oracle and report match perfectly, no problem at all
# if they DON'T, cases:
# 1. oracle reports void that analysis doesn't detect
# 2. analysis reports void that oracle doesn't have

# tp = analysis picked void; location & center match oracle's.
# fp = analysis picked void; info not reflected in oracle.
# tn = analysis didn't find void in design; no such void in oracle.
# fn = analysis didn't find void; void recorded in oracle 

# need to remove info when it matches a case

# t=true, f=false. p=positive, n=negative
# for each filename in report
    # if 'NO' in report and no entry for filename in oracle: tn 
    # if 'NO' in report but there is entry for filename in oracle: 
        # each entry in oracle counts as a fn
    # for each 'YES' report entry in filename
        # if entry matches entry in oracle, tp. remove entry from oracle.
        # if no such entry in oracle, fp. 
records = 0
for filename in report:
    #print(filename)
    #records += 1
    #print(filename)
    if len(report[filename])==1 and report[filename][0][0] == 'NO':
        records+=1
        if filename not in oracle:
            #print(f"adding tn: {filename},only one entry? {len(report[filename])==1}")
            tn +=1
        if filename in oracle:
            print(f'adding fn: {filename},theres {len(oracle[filename])} entries for this file in oracle')
            fn += len(oracle[filename])
            del oracle[filename]

    if report[filename][0][0]=='YES':
        #print('report thinks p')
        for entry in report[filename]:
            #print(entry[1])
            records+=1
            if filename not in oracle:
                
                print(f'fp: {filename} has {len(report[filename])} entries, but not in oracle')
                fp +=len(report[filename])
                break
            else:
                found = False
                for id in range(len(oracle[filename])):
                    entryo = oracle[filename][id]
                    found = compare(entry,entryo)
                    #print(f'entry \n{entry} matches oracle entry \n{entryo}? \n{found}')
                    if found:
                        #print('it matches oracle')
                        break
                # break continues here
                #print("continueing ")
                if not found:
                    print(f'fp: {filename}: entry {entry[1]} does not match oracle')
                    fp += 1
                else:
                    del oracle[filename][id]
                    tp+=1
                    #print('adding tp')
                    continue

num_proc_err = 0
for filename in err:
    if filename in oracle:
        num_proc_err+=len(oracle[filename])
        del oracle[filename]
for entry in oracle:
    amt = len(oracle[entry])
    if amt > 0:
        print(f'fn: {entry,len(oracle[entry])} voids not identified')
    fn += amt
print("Metrics Report")
#print(f'Number of records: {records}')
print(f'tp = {tp}\ttn = {tn}\nfp = {fp}\tfn = {fn}')
#print(f'Accuracy: {accuracy(tp,tn,fp,fn)}')
print(f'Precision: {precision(tp,fp)}')
print(f'Recall: {recall(tp,fn)}')
print(f'F1: {f1(tp,fp,fn)}')

#if num_proc_err != 0:
print(f'# voids not evaluated due to irregularities: {num_proc_err}')
for e in err:
    print(e,end=' ')