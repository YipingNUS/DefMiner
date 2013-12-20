# annotate_clean.py
# read test output and print only the sentence which contains both term and definition
# this is for human to read directly instead of to display on webpage
# Yiping 2012

import os
import re
import sys

################################################
#                 Main Function                #
################################################

if __name__ == '__main__' :

    f = open(sys.argv[1] + '.out','r')
    f_out = open(sys.argv[1] + '.annotated','w+')
    results = f.readlines()
    f.close()

    empty_line = False
    line = ''
    prev = 'O'
    hasTerm = False
    hasDef = False

    count = 1

    for result in results:
        result = result.strip()
        #result = result.replace("  ", " ")
        result_list = result.split("\t")

        #print(len(result_list))
        if(len(result_list)>=50):
            #has term
            if(result_list[len(result_list)-1] == "TERM" and prev == "O"):
                line+= '<TERM> '
                hasTerm = True
		prev = "TERM"
            elif(result_list[len(result_list)-1] == "TERM" and prev == "DEF"):
                line+= '</DEF> <TERM> '
                hasTerm = True
                prev = "TERM"
            elif(result_list[len(result_list)-1] == "DEF" and prev == "O"):
                line+= '<DEF> '
                hasDef = True
                prev = "DEF"
            elif(result_list[len(result_list)-1] == "DEF" and prev == "TERM"):
                line+= '</TERM> <DEF> '
                hasDef = True
                prev = "DEF"
	    elif(result_list[len(result_list)-1] == "O" and prev != "O"):
                line+= '</'+prev+'> '
                prev = "O"
            #end if else

            line += result_list[0]
            line += ' '
	    if(empty_line == True):
            	empty_line = False
	
        if(len(result_list)<=1 and empty_line == False):
            if prev != "O":
                line += "</SPAN> "
                prev = "O"
            #end if
            if (hasTerm and hasDef):
	        f_out.write(line + "\n")
            #end if
            count += 1
            line = ''
            empty_line = True
            hasTerm = False
            hasDef = False

    f_out.close()
