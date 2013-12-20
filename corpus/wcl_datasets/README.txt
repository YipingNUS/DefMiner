========================================================================
Annotated datasets for Extracting Definitions and Hypernyms from the Web
======================================================================== 
    Roberto Navigli, Paola Velardi   and   Juana María Ruiz-Martínez
     SAPIENZA Universita' di Roma            University of Murcia
========================================================================

=== The Package ===

This package contains two folders:

* wikipedia
* ukwac

The wikipedia folder contains the positive (wiki_good.txt) and negative
(wiki_bad.txt) definition candidates extracted from Wikipedia. This is
an extension of the dataset described in:

Roberto Navigli, Paola Velardi, Juana María Ruiz-Martínez. 
  An Annotated Dataset for Extracting Definitions and Hypernyms from the Web. 
  LREC 2010, Valletta, Malta, May 19-21, 2010, pp. 3716-3722

The ukwac folder contains candidate definitions for over 300,000 sentences 
from the ukWaC Web corpus (ukwac_testset.txt) in which occur any of 239 
domain terms selected from the terminology of four different domains 
(ukwac_terms.txt). To estimate recall, we manually checked 50,000 of 
these sentences and identified 99 definitional sentences 
(ukwac_estimated_recall.txt).

A description of the datasets and their use to learn Word-Class Lattices,
classify definitions and extract hypernyms is provided in:

Roberto Navigli, Paola Velardi. Learning Word-Class Lattices for 
  Definition and Hypernym Extraction. Proc. of the 48th Annual Meeting of 
  the Association for Computational Linguistics (ACL 2010), Uppsala, Sweden, 
  July 11-16, 2010, pp. 1318-1327

Please cite this paper to refer to the two datasets and the WCL algorithm.
The LREC paper should be cited only to refer to the Wikipedia annotated 
dataset.

=== Dataset Format ===

In each dataset, a candidate definition is described by two lines. The first 
line, starting with a # symbol, is the original sentence occurring in the
corresponding corpus. The second line contains: 

1) the term being defined (in non-definitional Wikipedia sentences 
   preceded by !)
2) colon
3) a part-of-speech tagged and possibly annotated sentence whose
   tokens are in tab-separated format.

In both lines, the term being defined is replaced by the TARGET token.
An example follows:

# TARGET is the part of the process whereby you remove the instrumental " artefacts " as well as apply sophisticated software techniques in order to manipulated the images .
image_processing:NP_NN_TARGET   VP_VBZ_is       NP_DT_the       NP_NN_part      PP_IN_of        PP_DT_the       PP_NN_process   ADVP_WRB_whereby        NP_PP_you       VP_VV_remove    NP_DT_the       NP_JJ_instrumental      NP_``_" NP_NNS_artefacts        ''_"    PP_IN_as        ADVP_RB_well    ADVP_RB_as      VP_VV_apply     NP_JJ_sophisticated     NP_NN_software  NP_NNS_techniques       PP_IN_in        PP_NN_order     PP_TO_to        PP_VVN_manipulated      NP_DT_the       NP_NNS_images   SENT_.

Each token in the second line is composed of three parts (separated by
the _ symbol):

* chunk (e.g. NP)
* part of speech (e.g. DT)
* lemma (e.g. the)

Annotated definitional sentences (such as those in wikipedia/wiki_good.txt)
include additional tokens: <RGET>, <VERB>, <GENUS>, <REST>. Each specifies
the start of a specific definition field (Definiendum, Definitor, Definiens and Rest,
respectively). Additional <HYPER> and </HYPER> tags enclose the hypernym(s) 
manually identified in the definition.

Note that some definitions (especially from Wikipedia) do not have the right
encoding for pronunciation symbols and non-standard symbols. This does not
affect the dataset, as they either occur within parentheses (whose content is
discarded to learn our WCL models) or did not affect part-of-speech tagging.
