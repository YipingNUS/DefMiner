# translate_wcl.py
# parse wcl corpus, prepare input to our system
# Yiping 2012

import re
import random
################################################
#                 Main Function                #
################################################


if __name__ == '__main__' : 
    
    #Parameters
    good_path    = './wikipedia/wiki_good.txt' #location of the documents
    bad_path = './wikipedia/wiki_bad.txt'
    #open file for reading
    f = open(good_path,'r')
    #read all the lines and store them in a list
    sentences = f.readlines()
    #file no longer needs to be open
    f.close()
    
    f = open("./wiki_good_yp.txt","w+")
    print(len(sentences))
    for sentence in sentences:
	sentence = sentence.strip()
	if len(sentence)>1 and not sentence.startswith("#"):
	    new_sent = ""
	    startDef = False
	    tokens = sentence.split("\t")
	    target = tokens[0]
	    target = target[:target.find(":")]
	    for token in tokens:
		if '_' in token:
		    word = token[token.rfind('_')+1:]
		    if not startDef:
		        new_sent += word + " "
		    else:
			new_sent += word + "/DEF "
			startDef = False
		if token == "<GENUS>":
		    startDef = True
	    #f.write("\n".join(tokens))
	    new_sent = new_sent.replace("TARGET", target+"/TERM")
	    new_sent = new_sent[:-1] + "/O"
	    f.write(new_sent+"\n")
	else:
	    pass#f.write(sentence)
    f.close()  

    #open file for reading
    f = open(bad_path,'r')
    #read all the lines and store them in a list
    sentences = f.readlines()
    #file no longer needs to be open
    f.close()
    
    f = open("./wiki_bad_yp.txt","w+")
    print(len(sentences))
    for sentence in sentences:
	sentence = sentence.strip()
	if len(sentence)>1 and not sentence.startswith("#"):
	    new_sent = ""
	    startDef = False
	    tokens = sentence.split("\t")
	    target = tokens[0]
	    target = target[1:target.find(":")]
	    for token in tokens:
		if '_' in token:
		    word = token[token.rfind('_')+1:]
		    if not startDef:
		        new_sent += word + " "
		    else:
			new_sent += word + "/DEF "
			startDef = False
		if token == "<GENUS>":
		    startDef = True
	    #f.write("\n".join(tokens))
	    new_sent = new_sent.replace("TARGET", target)
	    new_sent = new_sent[:-1]
	    f.write(new_sent+"\n")
	else:
	    pass#f.write(sentence)
    f.close()  
