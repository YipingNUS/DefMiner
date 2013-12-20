# this file is outdated, please refer to cv version
# crf_learn.py
# generate crfpp input 
# input: annotated sentences
# Yiping 2012

import os
from multiprocessing import Pool
import re
import nltk
import math
import random 
from nltk.corpus import conll2000 
from nltk.chunk import ne_chunk

unigram_lm = {}
#keyphrase dictionary
kp_dictionary = {}
term_dictionary = {}
definition_dictionary = {}
patterns = []
#negative feature: containing pronoun
pronouns = []
#ngrams from wcl positive corpus
_4grams = []
_5grams = []
_6grams = []
_7grams = []
_8grams = []

# original:
# columns: word | postag | stemmed lexical | suffix | in term dictionary | 
# in definition dictionary | capitalized | all caps | mixed case | 
# captilized character with period (H.) | ends in digit | contains hyphen |
# len of word | 
# 22/07/2012:
# in keyphrase dictionary | distance to beginning of document | len of sentence (# words) |
# pattern type | distance to pattern | first word | head word | NER chunktag | 
# (other structural features)
# chunktag

class BigramChunker(nltk.ChunkParserI):
    def __init__(self, train_sents):
        train_data = [[(t,c) for w,t,c in nltk.chunk.tree2conlltags(sent)] for sent in train_sents]
        self.tagger = nltk.BigramTagger(train_data)

    def parse(self, sentence):
        pos_tags = [pos for (word,pos) in sentence]
        tagged_pos_tags = self.tagger.tag(pos_tags)
        chunktags = [chunktag for (pos, chunktag) in tagged_pos_tags]
        conlltags = [(word, pos, chunktag) for ((word,pos),chunktag) in zip(sentence, chunktags)]
        #return nltk.chunk.conlltags2tree(conlltags)
        return conlltags

train_sents = conll2000.chunked_sents('train.txt',chunk_types=['NP'])
np_chunker = BigramChunker(train_sents)

#data[0]:metadata data[1]:word data[2]:pos data[3]:chunktag data[4]:outtag data[5]:shallowParse data[6]:NE
def Map(data):

    line = data[1]

    section_header = "OUT"
    section_id = "-1"
    sent_id = -1
    #sent index within section 
    sent_id_in_sec= -1

    parts = data[0].split(" $ ")
    if(len(parts)==5):
	section_header = parts[1]
        section_id = parts[2]
        sent_id = parts[3]
        #sent index within section 
        sent_id_in_sec= parts[4]

    #initialize results
    results = []	 

    #need to tokenize here
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
    #determine whether the sentence contains a pattern
    pattern_lookup = ["ABSENT","ABSENT","ABSENT","ABSENT","ABSENT","ABSENT","ABSENT","ABSENT","ABSENT","ABSENT","ABSENT"]
    for kk in range(len(patterns)):
     	pattern = patterns[kk]
       	#process the regular expression 
        #find all the place holders
        pattern = pattern.replace("\n","",1)
        #determine the type of pattern
        #type 1: <term> <pattern> <definition>
        #type 2: <definition> <pattern> <term>
        #ptype = pattern[1:2]
        ptype = str(kk)
        splitter = re.compile('\s?<.*?>,?\s?')
        segments = splitter.split(pattern)
        #the matchStr to look for
        matchStr ='.{2,50} '
        for segment in segments:
            # to avoid the special cases where single space, comma or some 
            # other characters are parsed as a segment  
            if (len(segment)>=2 or (len(segment)==1 and segment.count('n')== 0)):
                matchStr +=  segment +' .{2,80} '
        match = re.compile(matchStr)
	occurances = match.findall(line)
	if(len(occurances)>0):
	    #print(occurance)
	    #pattern_type = ptype
	    #pattern_index = len(nltk.word_tokenize(line[:line.index(segments[2])]))
	    pattern_lookup[kk] = "PRESENT"

    if(len(words)>=1):
        first_word = words[0].lower()
    else:
	first_word = "NONE"
    sentence_len = len(words)
    '''	    
    if(len(tokens)>5):
        sentence_index = int(tokens[0])
	sentence_len = int(tokens[1])
	pattern_type = tokens[2]
	#the index of the pattern in the string
	pattern_index = int(tokens[3])
	first_word = tokens[4].split('/')[0].lower()
    else:
	print('The line is too short (below 3 tokens)')
    '''

    #term frequency, extracted from input file
    #tfs = []
    #chunk tags BIO + Term / Def
    '''
    lastTag = "O"
    for i in range(len(tokens)):
        #elements = tokens[i].split('/')
	index = tokens[i].rfind('/')
	lastToken = tokens[i][index+1:]
	if(lastToken == "TERM"):
	    chunkTags.append('TERM')
	    words.append(tokens[i][:index])
	    lastTag = "TERM"
	elif(lastToken == "DEF"):
	    chunkTags.append('DEF')
	    words.append(tokens[i][:index])
	    lastTag = "DEF"
	elif(lastToken != "O" and lastTag == "DEF" ):#the chunkTag not specified
            chunkTags.append('DEF')	   
            words.append(tokens[i])   
	elif(lastToken == "O"):
            chunkTags.append('O')
            words.append(tokens[i][:index])
	    lastTag = "O"	    
	else:
	    chunkTags.append('O')
            words.append(tokens[i])
            lastTag = "O"
    '''
    outputTags = data[4].split(" ")
    if(len(outputTags)!=len(words)):
	print(str(len(outputTags))+":"+str(len(words)))
    #if(len(outputTags)<len(words)):
	#outputTags.append("O")
    #pos tagging	
    #poss = nltk.pos_tag(words)
    postags = data[2].split(" ")
    #np_parsed = np_chunker.parse(poss)
    shallowtags = data[3].split(" ")

    ne_tags = data[6].split(" ")

    ##########################
    ##Shallow Parse Features##
    parse_str = data[5]
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
	starts_with_NP = 'X'
    if(parse_str.startswith('ADVP') and 'NP' in parse_str[:10]):
	starts_with_ADVP = 'X'	
    if(short_str.startswith('PP NP')):
	starts_with_PPNP = 'X'
    if(short_str.startswith('the NP') or short_str.startswith('a NP') or short_str.startswith('an NP')):
	starts_with_DTNP = 'X'
    regex = re.compile("NP (is|are|was|were) ")
    if(len(regex.findall(short_str))>0):
	has_NPIS = 'X'	
    regex = re.compile("NP : (the |The |a |A |an |An )?NP")
    if(len(regex.findall(short_str))>0):
	has_NPiNP = 'X'
    regex = re.compile("NP (is|are|was|were) (the |a |any |some|an )?NP")
    if(len(regex.findall(short_str))>0):
	has_NPISNP = 'X'
    regex = re.compile("(refer|refers) to (the |The |a |A |an |An )?NP")
    if(len(regex.findall(short_str))>0):
	has_refer_to = 'X'
    regex = re.compile("NP (is|are|was|were) (the |a |any |some|an )?NP (of|that|which|for)")
    if(len(regex.findall(short_str))>0):
	has_NPISNPPP = 'X'
    regex = re.compile("NP (or|,) (the )?NP")
    if(len(regex.findall(short_str))>0):
	has_NPorNP = 'X'
    regex = re.compile(" known as (the )?NP")
    if(len(regex.findall(short_str))>0):
	has_known_as = 'X'
    regex = re.compile("NP of (the |a )?NP")
    if(len(regex.findall(short_str))>0):
	has_NPofNP = 'X'
    regex = re.compile("NP \( .{0,5}NP \)")
    if(len(regex.findall(short_str))>0):
	has_NPBRNPBR = 'X'
    regex = re.compile("NP (the|a|any|some|an) NP")
    if(len(regex.findall(short_str))>0):
        has_NPaNP = 'X'
    regex = re.compile("NP (consist|consists) .{0,5}(the |a |any |some|an )?NP")
    if(len(regex.findall(short_str))>0):
        has_NPconsistNP = 'X'
    regex = re.compile("(NP )?(defined|Defined) (as |by )?(the |a |any |some|an )?NP")
    if(len(regex.findall(short_str))>0):
        has_NPdefineNP = 'X' 
	#print("Found: "+ short_str)

    for _4gram in _4grams:
	if _4gram.strip()[:-3] in short_str:
	    in_4gram = 'N'
    for _5gram in _5grams:
        if _5gram.strip()[:-3] in short_str:
            in_5gram = 'N'
    for _6gram in _6grams:
        if _6gram.strip()[:-3] in short_str:
            in_6gram = 'N'
    for _7gram in _7grams:
        if _7gram[:-3] in short_str:
            in_7gram = 'N'
    for _8gram in _8grams:
        if _8gram[:-3] in short_str:
            in_8gram = 'N'

    ##Shallow Parse Features##
    ##########################

    #TODO: this can be useful, returns tree structure
    #ne_parsed = ne_chunk(poss)
    
    #postags = [pos for (word,pos) in poss]
    #chunktags_np = [chunktag for (word,pos,chunktag) in np_parsed]
    #chunktags_ne = [chunktag for (word,chunktag) in ne_parsed]
    started = True
    temp_result = []

    #general purpose stemmer 
    porter = nltk.PorterStemmer()

    #current index in the original str
    current_index = 0
    #obtain the chunk tags
    for i in range(len(words)):

	#store the features for current word in a dictionary
	all_features = {}
	
        #stemmed word
	stem = porter.stem(words[i])

	#suffix (if ends with ...)
	if words[i].endswith('ion') or words[i].endswith('ity') or words[i].endswith('tor') or words[i].endswith('ics') or words[i].endswith('ment') or words[i].endswith('ive') or words[i].endswith('ic'):
	    suffix = 1
	else:
	    suffix = 0

        
	#look up term dictionary
	if term_dictionary.has_key(words[i]) or term_dictionary.has_key(words[i].title()):
	    in_term_dic = 1
	else:
	    in_term_dic = 0

        #look up definition dictionary
        if definition_dictionary.has_key(words[i]) or definition_dictionary.has_key(words[i].title()):      
            in_def_dic = 1
        else: 
            in_def_dic = 0
	
        #look up keyphrase dictionary
        if kp_dictionary.has_key(words[i]) or kp_dictionary.has_key(words[i].title()):      
            in_kp_dic = 1
        else: 
            in_kp_dic = 0

	#below are all shape features
	capitalized = 0
	all_caps = 0
	mixed_cases = 0
	cap_with_period = 0
	with_digit = 0
	hyphen = 0
	length = words[i].__len__()

	capitalizedLetter = re.compile('[A-Z]')
	digit = re.compile('[0-9]')
	
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
	
	#the relative position with the pattern
	relative_pos = current_index - pattern_index
 	#calculate tf.idf feature. need normalizing to integer value
	if unigram_lm.has_key(words[i]):
	    #TODO:the number of documents hard coded as 10000
	    idf = math.log(10000.0/unigram_lm[words[i]])
	    #smoothing assume occur once	
	else:
 	    idf = math.log(1000000)
	#normalize idf
	if(idf<-5):
	    normalized_idf = '0'
	elif(idf>=-5 and idf<-2):
	    normalized_idf = '1'
        elif(idf>=-2 and idf<0):
            normalized_idf = '2'
        elif(idf>=0 and idf<1):
            normalized_idf = '3'
        elif(idf>=1 and idf<2):
            normalized_idf = '4'
        elif(idf>=2 and idf<3):
            normalized_idf = '5'
        elif(idf>=3 and idf<6):
            normalized_idf = '6'
	else:
	    normalized_idf = '7'

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
		
	#store the value of the features in the dictionary
	all_features['word'] = words[i]
	all_features['pos'] = postags[i]
	all_features['stem'] = stem
	all_features['suffix'] = suffix
	all_features['outputTag'] = outputTags[i]
	all_features['in_term_dictionary'] = in_term_dic
	all_features['in_definition_dictionary'] = in_def_dic
	all_features['length'] = words[i].__len__()/10
	all_features['capitalized'] = capitalized
    	all_features['all_caps'] = all_caps
    	all_features['mixed_cases'] = mixed_cases
    	all_features['cap_with_period'] = cap_with_period
    	all_features['with_digit'] = with_digit
    	all_features['hyphen'] = hyphen
	#added on 23.07.2012
	all_features['in_keyphrase_dictionary'] = in_kp_dic
	all_features['sentence_length'] = sentence_len
	all_features['first_word'] = first_word
	for kk in range(len(pattern_lookup)):
	    all_features[str(kk)] = pattern_lookup[kk]
	all_features['pattern_type'] = pattern_type
	all_features['pattern_index'] = pattern_index
	all_features['relative_pos'] = relative_pos
	all_features['normalized_idf'] = normalized_idf	
#added on 27.09.2012
	all_features['shallow_tag'] = shallowtags[i]
	all_features['word_position'] = i
	#added on 26.10.2012
	all_features['has_pronoun'] = has_pronoun
	#added on 30 Nov 2012
	all_features['section_id'] = section_id
	all_features['section_header'] = section_header
	all_features['sent_id'] = sent_id
	all_features['sent_id_in_sec'] = sent_id_in_sec
	#TODO:shallow parse features
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
	#added after analyzing errors 25/12/2012
	all_features['has_NPaNP'] = has_NPaNP
	all_features['has_NPconsistNP'] = has_NPconsistNP
	all_features['has_NPdefineNP'] = has_NPdefineNP
	all_features['has_ie'] = has_ie
	all_features['in_4gram'] = in_4gram
	all_features['in_5gram'] = in_5gram
	all_features['in_6gram'] = in_6gram
	all_features['in_7gram'] = in_7gram
	all_features['in_8gram'] = in_8gram
	#added on 4/1/2013 to build term&definition classifier
	all_features['first_10_word'] = first_10_word
	all_features['is_NP'] = is_NP
	all_features['is_head_NP'] = is_head_NP
	all_features['before_pattern'] = before_pattern
	all_features['NE'] = ne_tags[i]
	#print(all_features)
      	results.append(all_features)

	current_index += words[i].__len__() + 1
    #print(len(results))
    return results
    	
#TODO: merge the definitions for the same term from different documents
#this method is postponed because I haven't figure out how to get the term 
def Reduce(docid_term_definition) :
    tuples = []
    return tuples
	


################################################
#                 Main Function                #
################################################


if __name__ == '__main__' : 
    
    #Parameters
    #training_path = './corpus/wikiDef/input/annotated' #location of the documents
    #training_path = './corpus/wikiDef/final1000.annotated'
    #training_path = './corpus/wcl_datasets/input/annotated'
    training_path = './corpus/annotate/annotated'
    workers = 8

    print('reading stop words...')
    #load the stopwords
    f_stop = open('dictionary/stopwords')
    stopwords = f_stop.readlines()
    stopwords_str = ' '.join(stopwords)
    print('read ' + str(len(stopwords)) + ' stopwords.' )
 
    print('reading unigram language model...')
    f_uni = open('./ngram/acl.wfreq')
    unigram = f_uni.readlines()
    for line in unigram:
	elements = line.strip().split(' ')
	if(len(elements)>=2):
       	    entry = elements[0]	
	    count = int(elements[1])
	    unigram_lm[entry] = count
    print('read ' + str(len(unigram_lm)) + ' entries in unigram.')
    #print(unigram_lm['this'])

    #load the dictionary for keyphrases extracted by kea
    f_kp = open('./dictionary/acl_keyphrase.txt')
    kps = f_kp.readlines()
    for kp in kps:
        kp = kp.strip()
        if kp not in stopwords_str:
            kp_dictionary[kp] = 1

    f_kp.close()

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
    ##reading the corpus, including .word, .pos, .chunk and .meta .parse

    f_word = open(training_path+".word")
    #read all the lines and store them in a list
    sents = f_word.readlines()
    #file no longer needs to be open
    f_word.close()
    
    #pos tags
    f_pos = open(training_path+".pos")
    #read all the lines and store them in a list
    poss = f_pos.readlines()
    #file no longer needs to be open
    f_pos.close()

    # read the shallow parsing chunk for each word
    f_chunk = open(training_path+".chunk")
    #read all the lines and store them in a list
    chunks = f_chunk.readlines()
    #file no longer needs to be open
    f_chunk.close()

    #read the sentence and section information
    f_meta = open(training_path+".meta")
    #read all the lines and store them in a list
    metas = f_meta.readlines()
    #file no longer needs to be open
    f_meta.close()

    #read the output tag
    f_tag = open(training_path+".tag")
    #read all the lines and store them in a list
    tags = f_tag.readlines()
    #file no longer needs to be open
    f_tag.close()

    #read the shallow parse sequence
    f_parse = open(training_path+".parse")
    #read all the lines and store them in a list
    parses = f_parse.readlines()
    #file no longer needs to be open
    f_parse.close()

    #read the named entity sequence
    f_ne = open(training_path+".ne")
    #read all the lines and store them in a list
    nes = f_ne.readlines()
    #file no longer needs to be open
    f_ne.close()

    ##reading the corpus, including .word, .pos, .chunk and .meta
    #############################################################


    '''	
    #load the dictionary for term and definition
    f_term = open('./ngramtool/term.uni')
    terms = f_term.readlines()

    for term in terms:
	entry = term.split(' ')
	if entry[0].strip() not in stopwords_str:
       	    term_dictionary[entry[0]] = entry[1]

    f_term.close()

    f_def = open('./ngramtool/definition.uni')
    definitions = f_def.readlines()

    for definition in definitions:
        entry = definition.split(' ')
	if entry[0].strip() not in stopwords_str:
            definition_dictionary[entry[0]] = entry[1]

    f_def.close()
	
    #print(term_dictionary.keys())
    '''

    #allocate a thread pool
    #pool = Pool(processes=workers)

    #train_results = pool.map(Map,training)
    
    train_results = []
    for i in range(len(sents)):
	data = []
	data.append(metas[i].strip())
	data.append(sents[i].strip())
	data.append(poss[i].strip())
	data.append(chunks[i].strip())
  	data.append(tags[i].strip())
	data.append(parses[i].strip())
	data.append(nes[i].strip())
	train_results.append(Map(data))
   
    #random.shuffle(train_results)

    #############################################################
    ##reading the corpus, including .word, .pos, .chunk and .meta .parse
    training_path = './corpus/semi-supervised/annotated' 

    f_word = open(training_path+".word")
    #read all the lines and store them in a list
    sents = f_word.readlines()
    #file no longer needs to be open
    f_word.close()
    
    #pos tags
    f_pos = open(training_path+".pos")
    #read all the lines and store them in a list
    poss = f_pos.readlines()
    #file no longer needs to be open
    f_pos.close()

    # read the shallow parsing chunk for each word
    f_chunk = open(training_path+".chunk")
    #read all the lines and store them in a list
    chunks = f_chunk.readlines()
    #file no longer needs to be open
    f_chunk.close()

    #read the sentence and section information
    f_meta = open(training_path+".meta")
    #read all the lines and store them in a list
    metas = f_meta.readlines()
    #file no longer needs to be open
    f_meta.close()

    #read the output tag
    f_tag = open(training_path+".tag")
    #read all the lines and store them in a list
    tags = f_tag.readlines()
    #file no longer needs to be open
    f_tag.close()

    #read the shallow parse sequence
    f_parse = open(training_path+".parse")
    #read all the lines and store them in a list
    parses = f_parse.readlines()
    #file no longer needs to be open
    f_parse.close()

    #read the named entity sequence
    f_ne = open(training_path+".ne")
    #read all the lines and store them in a list
    nes = f_ne.readlines()
    #file no longer needs to be open
    f_ne.close()

    for i in range(len(sents)):
	data = []
	data.append(metas[i].strip())
	data.append(sents[i].strip())
	data.append(poss[i].strip())
	data.append(chunks[i].strip())
  	data.append(tags[i].strip())
	data.append(parses[i].strip())
	data.append(nes[i].strip())
	train_results.append(Map(data))

    ##reading the corpus, including .word, .pos, .chunk and .meta
    #############################################################	
    print 'Found ' + str(len(train_results)) + ' lines.'
    #print 'Found ' + str(len(sentence_results)) + 'sentences'
    
    #list of features to be used
    features =['word','pos','stem','suffix','capitalized','all_caps','mixed_cases','cap_with_period','with_digit','hyphen','length','in_keyphrase_dictionary','sentence_length','first_word','normalized_idf','shallow_tag','word_position','section_id','section_header','sent_id','sent_id_in_sec','pattern_type','pattern_index','has_pronoun','starts_with_NP','starts_with_ADVP','starts_with_PPNP','starts_with_DTNP','has_NPiNP','has_NPIS','has_NPISNP','has_refer_to','has_NPISNPPP','has_NPorNP','has_known_as','has_NPofNP','has_NPBRNPBR','has_NPaNP','has_NPconsistNP','has_NPdefineNP','has_ie','in_4gram','in_5gram','in_6gram','in_7gram','in_8gram','first_10_word','is_NP','is_head_NP','before_pattern']
    for k in range(11):
	features.append(str(k))

    features.append('NE')
    features.append('outputTag')

    #f = open("./CRF++-0.57/fyp/experiments/wcl/wcl_full.data","w+")
    f = open("./CRF++-0.57/fyp/experiments/acl-arc/annotate.data","w+")
    for sentence in train_results:
	for word in sentence:
	    is_complete = True
	    line = ''
	    for feature in features:
                
		if ' ' in str(word[feature]): 
		    word[feature] = '?'
		if(len(str(word[feature]))<1):
		    #error extracting feature
		    word[feature] = '?'
		line += str(word[feature]) + ' '
	    if(is_complete):
                f.write(line + '\n') 
	f.write('\n')

    f.close()
    '''
    f_train = open("./CRF++-0.57/fyp/experiments/wcl/train.data","w+")
    f_test = open("./CRF++-0.57/fyp/experiments/wcl/test.data","w+")
    for i in range(len(train_results)):
        sentence = train_results[i]
        for word in sentence:
	    is_complete = True
            line = ''
            for feature in features:
                line += str(word[feature]) + ' '
		if(len(str(word[feature]))<1):
		    #error extracting feature
		    is_complete = False
		if(' ' in str(word[feature])):
		    print("contain space!"+feature + ":" + str(word[feature]))
		    is_complete = False
	    if(is_complete):		
                if(i<0.9*len(train_results)):
                    f_train.write(line + '\n')
                else:
                    f_test.write(line+ '\n')
        if(i<0.9*len(train_results)):
            f_train.write('\n')
        else:
            f_test.write('\n')
    f_train.close()
    f_test.close()
    '''
