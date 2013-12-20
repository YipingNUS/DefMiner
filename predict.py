# predict.py
# generate crfpp input for input file
# input: preprocessed files (word, pos, chunktag, dependency, etc)
# Yiping 2013

import os
from multiprocessing import Pool
import re
#import nltk
import math
import random 
import sys
import getopt

unigram_lm = {}
#keyphrase dictionary
patterns = []
#negative feature: containing pronoun
pronouns = []
#ngrams from wcl positive corpus
_4grams = []
_5grams = []
_6grams = []
_7grams = []
_8grams = []

capitalizedLetter = re.compile('[A-Z]')
digit = re.compile('[0-9]')
OUT_TAG = "?"

def Map(data):
    ''' process a single sentence and extract features for each word
    
    Args:
        data[0]:word 
	data[1]:pos 
	data[2]:chunktag 
	data[3]:shallowParse sequence 
	data[4]:NE tag
	data[5]:dependency parent
	data[6]:dependency parent type
        data[7]:dependency path to root

    Return:
	dictionary[]: each dictionary contains the features for that word
    '''
    #initialize results
    results = []	 

    line = data[0]
    words = line.split(" ") 

    #whether the sentence contains pronouns
    has_pronoun = 0
    for pronoun in pronouns:
	pronoun = pronoun.strip()
	matchStr = "\W?"+pronoun+"\W"
	match = re.compile(matchStr)
	if(len(match.findall(line))>0):
	    has_pronoun = 1

    #has i.e.
    has_ie = '0'
    match = re.compile('i\.e\..{5,100}')
    if(len(match.findall(line))>0):
	has_ie = '1'

    pattern_type = -1
    pattern_index = -1	
    #determine whether the sentence contains a surface pattern
    pattern_lookup = ['0']*11  #initialize as not present for every pattern
    for i in range(len(patterns)):
     	pattern = patterns[i]
       	#process the regular expression 
        #find all the place holders
        pattern = pattern.replace("\n","",1)
        #determine the type of pattern
        #type 1: <term> <pattern> <definition>
        #type 2: <definition> <pattern> <term>
        #ptype = pattern[1:2]
        ptype = str(i)
        splitter = re.compile('\s?<.*?>,?\s?')
        segments = splitter.split(pattern)
        #the matchStr to look for
        matchStr ='.{2,50} '
        for segment in segments:
            # to avoid the special cases where single space, comma or some 
            # other characters are parsed as a segment  
            if (len(segment)>=2 or (len(segment)==1 and segment.count('1')== 0)):
                matchStr +=  segment +' .{2,80} '
        match = re.compile(matchStr)
	occurances = match.findall(line)
	if(len(occurances)>0):
	    #print(occurance)
	    #pattern_type = ptype
	    #pattern_index = len(nltk.word_tokenize(line[:line.index(segments[2])]))
	    pattern_lookup[i] = '1'
    #end for i in range

    if(len(words)>=1):
        first_word = words[0].lower()
    else:
	first_word = "EMPTY"
    sentence_len = len(words)

    postags = data[1].split(" ")
    shallowtags = data[2].split(" ")
    ne_tags = data[4].split(" ")
    parents = data[5].split(" ")
    ptypes = data[6].split(" ")
    dep_paths = data[7].split(" ")
	
    #####################################
    ##Shallow parsing sequence features##
    parse_str = data[3]
    short_str = parse_str.replace("ADVP","")
    short_str = short_str.replace("ADJP","")
    short_str = short_str.strip()
    #short_list = short_str.split(' ')	
    #print(parse_str)
    starts_with_NP = '0'
    starts_with_ADVP = '0'
    starts_with_PPNP = '0'
    starts_with_DTNP = '0'
    # NP : NP
    has_NPiNP = '0'
    # NP is
    has_NPIS = '0'
    # NP is * NP
    has_NPISNP = '0'
    # refer(s) to * NP
    has_refer_to = '0'
    # NP is * NP + of/that/which/for/and/PUNCTUATION
    has_NPISNPPP = '0'
    # NP or NP
    has_NPorNP = '0'
    # known as * NP
    has_known_as = '0'
    # NP of * NP
    has_NPofNP = '0'
    # NP ( NP ) 
    has_NPBRNPBR = '0'
    # NP a NP	
    has_NPaNP = '0'
    has_NPconsistNP = '0'
    has_NPdefineNP = '0'    
    #look up patterns appeared in wcl corpus
    in_4gram = '0'
    in_5gram = '0'
    in_6gram = '0'
    in_7gram = '0'
    in_8gram = '0'   
 
    if(short_str.startswith('NP')):
	starts_with_NP = '1'
    if(parse_str.startswith('ADVP') and 'NP' in parse_str[:10]):
	starts_with_ADVP = '1'	
    if(short_str.startswith('PP NP')):
	starts_with_PPNP = '1'
    if(short_str.startswith('the NP') or short_str.startswith('a NP') or short_str.startswith('an NP')):
	starts_with_DTNP = '1'
    regex = re.compile("NP (is|are|was|were) ")
    if(len(regex.findall(short_str))>0):
	has_NPIS = '1'	
    regex = re.compile("NP : (the |The |a |A |an |An )?NP")
    if(len(regex.findall(short_str))>0):
	has_NPiNP = '1'
    regex = re.compile("NP (is|are|was|were) (the |a |any |some|an )?NP")
    if(len(regex.findall(short_str))>0):
	has_NPISNP = '1'
    regex = re.compile("(refer|refers) to (the |The |a |A |an |An )?NP")
    if(len(regex.findall(short_str))>0):
	has_refer_to = '1'
    regex = re.compile("NP (is|are|was|were) (the |a |any |some|an )?NP (of|that|which|for)")
    if(len(regex.findall(short_str))>0):
	has_NPISNPPP = '1'
    regex = re.compile("NP (or|,) (the )?NP")
    if(len(regex.findall(short_str))>0):
	has_NPorNP = '1'
    regex = re.compile(" known as (the )?NP")
    if(len(regex.findall(short_str))>0):
	has_known_as = '1'
    regex = re.compile("NP of (the |a )?NP")
    if(len(regex.findall(short_str))>0):
	has_NPofNP = '1'
    regex = re.compile("NP \( .{0,5}NP \)")
    if(len(regex.findall(short_str))>0):
	has_NPBRNPBR = '1'
    regex = re.compile("NP (the|a|any|some|an) NP")
    if(len(regex.findall(short_str))>0):
        has_NPaNP = '1'
    regex = re.compile("NP (consist|consists) .{0,5}(the |a |any |some|an )?NP")
    if(len(regex.findall(short_str))>0):
        has_NPconsistNP = '1'
    regex = re.compile("(NP )?(defined|Defined) (as |by )?(the |a |any |some|an )?NP")
    if(len(regex.findall(short_str))>0):
        has_NPdefineNP = '1' 
	#print("Found: "+ short_str)

    for _4gram in _4grams:
	if _4gram.strip()[:-3] in short_str:
	    in_4gram = '1'
    for _5gram in _5grams:
        if _5gram.strip()[:-3] in short_str:
            in_5gram = '1'
    for _6gram in _6grams:
        if _6gram.strip()[:-3] in short_str:
            in_6gram = '1'
    for _7gram in _7grams:
        if _7gram[:-3] in short_str:
            in_7gram = '1'
    for _8gram in _8grams:
        if _8gram[:-3] in short_str:
            in_8gram = '1'

    ##Shallow parsing sequence features##
    #####################################

    started = True
    temp_result = []

    #general purpose stemmer 
    #porter = nltk.PorterStemmer()

    #current index in the original str
    current_index = 0

    # position features are not used
    section_header = "O"  # no section header found
    section_id = "-1"
    sent_id = -1
    #sent index within section 
    sent_id_in_sec= -1

    ############################################
    ## below extracts all word level features ##
    for i in range(len(words)):

	#store the features for current word in a dictionary
	all_features = {}

        #stemmed word
        if(len(words[i])>8):
	    stem = words[i][:-2]
        else:
            stem = words[i]

	#suffix (if ends with ...)
	if words[i].endswith('ion') or words[i].endswith('ity') or words[i].endswith('tor') or words[i].endswith('ics') or words[i].endswith('ment') or words[i].endswith('ive') or words[i].endswith('ic'):
	    suffix = 1
	else:
	    suffix = 0

	##################################
	##       shape features         ##
	capitalized = 0
	all_caps = 0
	mixed_cases = 0
	cap_with_period = 0
	with_digit = 0
	hyphen = 0
	length = words[i].__len__()

	#captalized
	if capitalizedLetter.search(words[i][0:1]):
	    capitalized = 1
	    #all captalized
	    if length > 1 and capitalizedLetter.search(words[i][1:]):
		all_caps = 1
	#some letter is captalized, not first one
	elif length >1 and capitalizedLetter.search(words[i][1:]):
	    mixed_cases = 1
	#last character '.' and last but one is capitalized
	if length >2 and capitalizedLetter.search(words[i][length-2:]) and words[i][length-1:length] == '\.':
	    cap_with_period = 1
	#contains digit
	if digit.search(words[i]):
	    with_digit = 1
	#contains hyphen
	if '-' in words[i]:
	    hyphen = 1	 	

        #######################################
        ##     position features            ###
	#the relative position with the pattern
	relative_pos = current_index - pattern_index

	#if the word is in the first 10 words of the sentence, for term classifier
	if(i<10 and i<0.4*len(words)):
	    first_10_word = '1'
	else:
	    first_10_word = '0'
	#if the word is part of a NP
	if(shallowtags[i].endswith('NP')):
	    is_NP = '1'
	else:
	    is_NP = '0'
	if(is_NP=='1' and first_10_word=='1'):
	    is_head_NP = '1'
	else:
	    is_head_NP = '0'
        #if the token is directly before 'is a' or 'is the'
	before_pattern = '0'
	if(i<len(words)-5):
	    context_str = ''
	    for k in range(5):
		context_str += words[i+k] + ' '
	    if('is a' in context_str or 'is the' in context_str):
		before_pattern = '1'
		#print(context_str)
	
	#####################################
        ####      dependency features   #####
	ancestor = "aBSENT"  # the root of the word
 
	#print dep_path_str		    
	#store the value of the features in the dictionary
	all_features['word'] = words[i]
	all_features['pos'] = postags[i]
	all_features['stem'] = stem
	all_features['suffix'] = suffix
	all_features['outputTag'] = OUT_TAG
	all_features['length'] = len(words)/10
	all_features['capitalized'] = capitalized
    	all_features['all_caps'] = all_caps
    	all_features['mixed_cases'] = mixed_cases
    	all_features['cap_with_period'] = cap_with_period
    	all_features['with_digit'] = with_digit
    	all_features['hyphen'] = hyphen
	all_features['sentence_length'] = sentence_len
	all_features['first_word'] = first_word
	for kk in range(len(pattern_lookup)):
	    all_features[str(kk)] = pattern_lookup[kk]
	all_features['pattern_type'] = pattern_type
	all_features['pattern_index'] = pattern_index
	all_features['relative_pos'] = relative_pos
	all_features['shallow_tag'] = shallowtags[i]
	all_features['word_position'] = i
	all_features['has_pronoun'] = has_pronoun
	all_features['section_id'] = section_id
	all_features['section_header'] = section_header
	all_features['sent_id'] = sent_id
	all_features['sent_id_in_sec'] = sent_id_in_sec
        #shallow parsing sequence features
	all_features['starts_with_NP'] = starts_with_NP
        all_features['starts_with_ADVP'] = starts_with_ADVP 
        all_features['starts_with_PPNP'] = starts_with_PPNP
        all_features['starts_with_DTNP'] = starts_with_DTNP
        # NP : NP
        all_features['has_NPiNP'] = has_NPiNP
        # NP is
        all_features['has_NPIS'] = has_NPIS
        # NP is * NP
        all_features['has_NPISNP'] = has_NPISNP
        # refer(s) to * NP
        all_features['has_refer_to'] = has_refer_to
        # NP is * NP + of/that/which/for/and/PUNCTUATION
        all_features['has_NPISNPPP'] = has_NPISNPPP
        # NP or NP
        all_features['has_NPorNP'] = has_NPorNP
        # known as * NP
        all_features['has_known_as'] = has_known_as
        # NP of * NP	
        all_features['has_NPofNP'] = has_NPofNP
        # NP ( NP ) 
        all_features['has_NPBRNPBR'] = has_NPBRNPBR
	all_features['has_NPaNP'] = has_NPaNP
	all_features['has_NPconsistNP'] = has_NPconsistNP
	all_features['has_NPdefineNP'] = has_NPdefineNP
	all_features['has_ie'] = has_ie
	all_features['in_4gram'] = in_4gram
	all_features['in_5gram'] = in_5gram
	all_features['in_6gram'] = in_6gram
	all_features['in_7gram'] = in_7gram
	all_features['in_8gram'] = in_8gram
	all_features['first_10_word'] = first_10_word
	all_features['is_NP'] = is_NP
	all_features['is_head_NP'] = is_head_NP
	all_features['before_pattern'] = before_pattern
	if len(ne_tags)>0:
	    all_features['NE'] = ne_tags[i]
	else:
	    print "!!!"
	#dependency features
	all_features['root'] = ancestor
        all_features['parent_word'] = parents[i]
	all_features['parent_type'] = ptypes[i]
	all_features['dep_path_str'] = dep_paths[i]

      	results.append(all_features)

	current_index += words[i].__len__() + 1
    #print(len(results))
    return results
#end of map	


################################################
#                 Main Function                #
################################################

def usage():
  print 'Usage: '+sys.argv[0]+' -i <file>'

if __name__ == '__main__' : 
   
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:', ['help', 'input file='])
        if not opts or len(opts) != 1:
          print 'Wrong number of options supplied'
          usage()
          sys.exit(2)

        #get sys arguments
        input_path = opts[0][1]
        
        print "input_path=%s" % input_path
        ''' now done by bash script
        #find the folder containing all the preprocessing files
        if '.' in input_file:
            input_folder = input_file[:input_file.rfind('.')] + "_defminer"
        else:
            input_folder = input_file + "_defminer"
        if "/" in input_folder:
            filename = input_folder[input_folder.rfind('/')+1:]
        else:
            filename = input_folder
        input_path = input_folder + "/" + filename
        '''
    except getopt.GetoptError,e:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)

    print "input file at %s" % input_path

    print('reading stop words...')
    #load the stopwords
    f_stop = open('dictionary/stopwords')
    stopwords = f_stop.readlines()
    stopwords_str = ' '.join(stopwords)
    print('read ' + str(len(stopwords)) + ' stopwords.' )
    
    #load the patterns
    f_pt = open('./pattern.txt')
    patterns = f_pt.readlines()
    f_pt.close()

    #load the pronouns
    f_pn = open('./pronoun.txt')
    pronouns = f_pn.readlines()
    f_pn.close()
    
    #load chunk ngrams from wcl corpus
    f = open('./corpus/wcl_datasets/ngram/4gram')
    _4grams = f.readlines()
    f.close()

    f = open('./corpus/wcl_datasets/ngram/5gram')
    _5grams = f.readlines()
    f.close()

    f = open('./corpus/wcl_datasets/ngram/6gram')
    _6grams = f.readlines()
    f.close()

    f = open('./corpus/wcl_datasets/ngram/7gram')
    _7grams = f.readlines()
    f.close()

    f = open('./corpus/wcl_datasets/ngram/8gram')
    _8grams = f.readlines()
    f.close()

    #############################################################
    ##reading the corpus, including .word, .pos, .chunk, .seq, 
    ##                              .ne, .parent, .ptype, .path

    # read words
    f_word = open(input_path+".word")
    sents = f_word.readlines()
    f_word.close()
    
    # read pos tags
    f_pos = open(input_path+".pos")
    poss = f_pos.readlines()
    f_pos.close()

    # read the shallow parsing chunk tags for each word
    f_chunk = open(input_path+".chunk")
    chunks = f_chunk.readlines()
    f_chunk.close()

    # read the shallow parse sequences
    f_parse = open(input_path+".seq")
    parses = f_parse.readlines()
    f_parse.close()

    # read the named entity sequence
    f_ne = open(input_path+".ne")
    nes = f_ne.readlines()
    f_ne.close()

    # read dependency parent word
    f_parent = open(input_path+".parent")
    parents = f_parent.readlines()
    f_parent.close()

    # read the dependency parent type
    f = open(input_path+".ptype")
    ptypes = f.readlines()
    f.close()

    # read the dependency path to root
    f = open(input_path+".path")
    paths = f.readlines()
    f.close()

    ## end reading input from files
    #############################################################

    print("Extract features for %d sentences" % len(sents))
 
    results = []
    for i in range(len(sents)):
	data = []
	data.append(sents[i].strip())
	data.append(poss[i].strip())
	data.append(chunks[i].strip())	
	data.append(parses[i].strip())
	#below will not be generated for fast mode
	data.append(nes[i].strip())
	data.append(parents[i].strip())
        data.append(ptypes[i].strip())
        data.append(paths[i].strip())
	results.append(Map(data))
    #end for loop prepare data   
	
    print 'Found ' + str(len(results)) + ' sentences.'
    #print 'Found ' + str(len(sentence_results)) + 'sentences'
    
    #list of features to be used
    features =['word','pos','stem','suffix','capitalized','all_caps','mixed_cases','cap_with_period','with_digit','hyphen','length','sentence_length','first_word','shallow_tag','word_position','section_id','section_header','sent_id','sent_id_in_sec','pattern_type','pattern_index','has_pronoun','starts_with_NP','starts_with_ADVP','starts_with_PPNP','starts_with_DTNP','has_NPiNP','has_NPIS','has_NPISNP','has_refer_to','has_NPISNPPP','has_NPorNP','has_known_as','has_NPofNP','has_NPBRNPBR','has_NPaNP','has_NPconsistNP','has_NPdefineNP','has_ie','in_4gram','in_5gram','in_6gram','in_7gram','in_8gram','first_10_word','is_NP','is_head_NP','NE','root']
    for k in range(11):
	features.append(str(k))

    features.append('parent_word')
    features.append('parent_type')
    features.append('dep_path_str')
    features.append('outputTag')
	
    print "Total %d features" % len(features)

    f = open(input_path + ".data","w+")

    for sentence in results:
	for word in sentence:
	    is_complete = True
	    line = ''
	    for feature in features:
                line += str(word[feature]) + ' '
		if(len(str(word[feature]))<1):
		    #error extracting feature
		    is_complete = False
                    print(str(feature) + " : " + str(word[feature]))
	    if(is_complete):
                f.write(line + '\n')
       
	f.write('\n')

    f.close()
    
#end of script
