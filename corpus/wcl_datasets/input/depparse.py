# depparse.py
# Allign the dependency parsing with the original sentence
# Yiping 2012

import os
from multiprocessing import Pool
import re
import nltk
import sys 	

################################################
#                 Main Function                #
################################################


if __name__ == '__main__' : 
    
    #Parameters
    dep_path    = './annotated.dependency' #location of the document
    word_path = './annotated.word'
    out_path = './annotated.dependency.post'

    f_dep = open(dep_path,"r")
    lines = f_dep.readlines()
    f_dep.close()

    f = open(word_path,"r")
    sents = f.readlines()
    f.close()

    temp_sents = [] #original sentence removing all capital letter and symbols
    temp_sent2=  '' #sentence in dependency parsing file after rm

    regex = "\(.{1,20}-\d(\d)*, .{1,20}-\d(\d)*\)" #regular expression to match dependency str
    
    for sent in sents:
	temp_sent1 = sent.strip()
	temp_sent1 = re.sub("\W","",temp_sent1)
	temp_sent1 = re.sub("[A-Z]","",temp_sent1)
	temp_sents.append(temp_sent1)
	#print temp_sent1

    matched = []
    dep_lists = []
    for i in range(len(sents)):
	matched.append(0)
	dep_lists.append({"NOT FOUND"})
 
    for i in range(len(lines)):
	line = lines[i]
	m = re.search(regex,line)
	if m:
	    continue 
	elif len(line)>2:
	    #print line
            temp_sent2 = line.strip()
            temp_sent2 = re.sub("\W","",temp_sent2)
            temp_sent2 = re.sub("[A-Z]","",temp_sent2)
	    #if(len(temp_sent2)<2):
	  	#print(line)
            for j in range(len(temp_sents)):
		temp_sent = temp_sents[j]
		if len(temp_sent2)>15: 
		    #if temp_sent.startswith(temp_sent2):
		        #print "match"
	   	    if temp_sent2 in temp_sent:
			#print "match"
			matched[j]=1
			i += 2
			if(len(lines[i].strip())>0):
			    dep_list = []
			while (len(lines[i].strip())>0): #not a space
			    dep_list.append(lines[i].strip())
			    i += 1
			dep_lists[j] = dep_list

    f = open(out_path, "w+")	
	 
    for i in range(len(sents)):
	#if matched[i] ==1 or matched[i] == 0:
	    #print "###"
	#if(len(dep_lists[i])==0):
	    #print dep_lists[i]
	print "\n".join(dep_lists[i])
	print ""
	f.write("\n".join(dep_lists[i]) + "\n\n")

    f.close() 
    #print(len(dep_lists))	
