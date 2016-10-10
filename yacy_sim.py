#!/usr/bin/python3

# TODO: Finish rebasing this against the YaCy JSON explain API.

import operator
import json
import math
from functools import reduce

# https://stackoverflow.com/questions/7948291/is-there-a-built-in-product-in-python
def prod(iterable):
    return reduce(operator.mul, iterable, 1)

def logSimulatedRelevance(result):
    print("Simulated ranking:", result)
    return result

# explainDump should be a parsed JSON object from YaCy's explain field for a result.
def simulateRelevance(explainDump, rankingParams, matchField = None, matchValue = None):
    
    if "Failure to meet condition" in explainDump["description"]:
        
        print("YaCy dumped ranking:", explainDump["value"])
        
        # This shows up for results that don't match the search query at all.  Return 0.0 relevance.
        return logSimulatedRelevance(0.0)
    
    if "weight(" in explainDump["description"]:
        
        # We've found a hint for what ranking rule a descendenat "boost" value maps to.
        # Therefore we grab that info for later.
        
        tempResult = explainDump["description"]
        
        # starting point: 
        "weight(inboundlinks_anchortext_txt:botball in 2088) [DefaultSimilarity], result of:"
        "weight(title:\"hillary clinton cnbc\" in 215) [ClassicSimilarity], result of:"
        
        tempResult = tempResult.split("(")[1]
        
        # now:
        "inboundlinks_anchortext_txt:botball in 2088) [DefaultSimilarity], result of:"
        "title:\"hillary clinton cnbc\" in 215) [ClassicSimilarity], result of:"
        
        tempResult = tempResult.split(")")[0]
        
        # now:
        "inboundlinks_anchortext_txt:botball in 2088"
        "title:\"hillary clinton cnbc\" in 215"
        
        if ":" not in tempResult:
            
            # no matchValue is specified for this particular ranking rule
            matchField = tempResult.split(" ")[0]
            matchValue = None
            
        else:
            
            matchField = tempResult.split(":")[0]
            
            tempResult = tempResult.split(":")[1]
            
            # now:
            "botball in 2088"
            "\"hillary clinton cnbc\" in 215"
            
            if '"' in tempResult:
                matchValue = tempResult.split('"')[1]
                # "hillary clinton cnbc"
            else:
                matchValue = tempResult.split(" ")[0]
                # "botball"
        
    if "details" in explainDump:
        
        children = explainDump["details"]
        
        childValues = [simulateRelevance(elem, rankingParams, matchField, matchValue) for elem in children]
        
        print("YaCy dumped ranking:", explainDump["value"])
        
    else:
        
        print("YaCy dumped ranking:", explainDump["value"])
        
        if explainDump["description"] == "boost":
            
            # This is a boost value that we may need to replace based on rankingParams.
            
            # Check whether there are any ranking rules for the matchField
            if matchField in rankingParams:
                
                # Check whether there is a specific ranking rule for the matchField/matchValue combination
                if matchValue is not None and matchValue in rankingParams[matchField]:
                    return logSimulatedRelevance(rankingParams[matchField][matchValue])
                
                # Check whether there is a wildcard ranking rule for the matchField
                if "*" in rankingParams[matchField]:
                    return logSimulatedRelevance(rankingParams[matchField]["*"])
                
            # We've encountered a boost value that we don't know how to replace.
            # This is probably because YaCy is configured to use a ranking rule that we're not considering in our simulation rankingParams.
            # Warn the user by printing a warning.
            print('WARNING: encountered an unrecognized boost for ' + json.dumps(matchField) + ':' + json.dumps(matchValue) + ".  YaCy may be configured to use a ranking rule that isn't being considered in the simulation.  This boost will be simulated as whatever value YaCy was set to use when the explain dump was generated.")
        
        return logSimulatedRelevance(explainDump["value"])
    
    if "sum of:" in explainDump["description"]:
        
        return logSimulatedRelevance(sum(childValues))
    
    if "product of:" in explainDump["description"]:
        
        return logSimulatedRelevance(prod(childValues))
    
    if "max of:" in explainDump["description"]:
        
        return logSimulatedRelevance(max(childValues))
    
    if "power of:" in explainDump["description"]:
        
        return logSimulatedRelevance(pow(childValues[0], childValues[1]))
    
    if "floor of:" in explainDump["description"]:
        
        return logSimulatedRelevance(math.floor(childValues[0]))
    
    if "with freq of:" in explainDump["description"]:
        
        # this is the tf() function in Solr.  It's unclear to me exactly how the math works, but its result shouldn't be dependent on a boost, so we can just use the dumped value rather than simulating it.
        return logSimulatedRelevance(explainDump["value"])
    
    if "result of:" in explainDump["description"]:
        
        # identity operation
        return logSimulatedRelevance(childValues[0])
    
    raise Exception("Unrecognized explainDump!:\n" + json.dumps(explainDump))

def testSimulateRelevance():
    
    with open("explainDumpTestCase1.json") as json_data:
        explainDump = json.load(json_data)
    
    rankingParams = {
    }
    
    #expectedRanking = 2.1493888E8
    #expectedRanking = 2.14938752E8
    expectedRanking = explainDump["value"]
    
    observedRanking = simulateRelevance(explainDump, rankingParams)
