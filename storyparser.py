import pyparsing
from pyparsing import alphas,alphanums
from pyparsing import Literal, Word, Group
from pyparsing import ZeroOrMore, OneOrMore, Optional, delimitedList
from pyparsing import StringEnd, Forward, Suppress, restOfLine

global grammar

def actionNTP(s, loc, toks):
    return "NTP",toks[0][0],toks[0][2]

def actionComment(s, loc, toks):
    return "COMMENT",toks[0][1]
 
def actionList(s, loc, toks):
    list = toks[0].asList()
    print "actionList:",list
    return "LIST", list

def define_grammar():
    global grammar
    one_expr = Forward()
    one_or_more_expr = Forward()
    zero_or_more_expr = Forward()

    anum = Word( alphas+"_", alphanums+"_" )    # Starts with a letter or underscore, can continue with numbers too
    nametype_expr = Group(anum + ":" + anum).setParseAction(actionNTP)
    comment_expr = Group(Literal("#") + restOfLine).setParseAction(actionComment)
    list_expr = Group(Suppress("[") + zero_or_more_expr + Optional(Suppress(",") + one_or_more_expr) + Suppress("]")).setParseAction(actionList)

    # Putting it all together.
    # Any earlier Forward-defined expressions must be assigned to using "<<" rather than "="
    # REMEMBER: You MUST put () around the whole RHS of << assignment, or the wrong thing happens
    one_expr << (list_expr | nametype_expr | comment_expr)
    # "|" is pyparsing's MatchFirst operator, so put most general matches at the end so they only gets matched if nothing else does
    # "^" is pyparsing's Or operator, which finds the longest match
    one_or_more_expr << (OneOrMore(one_expr))
    zero_or_more_expr << (ZeroOrMore(one_expr))
    zero_or_more_expr.validate() # Check for recursive loops (NOTE: Highly compute-intensive)

    final_expr = zero_or_more_expr + StringEnd()    # StringEnd() to force consumption of entire string (no trailing stuff)

    grammar = final_expr

def traverse(tree):
    # Called with a list, recurses through it
    # Called with a leaf, just executes it
    # print "traverse",type(tree),":",tree

    if(type(tree)==pyparsing.ParseResults): # pyparsing annoyingly returns subtrees not as plain lists
        tree = tree.asList()
    
    if(type(tree) == type([])):
        result = ""
        for item in tree:
            result = result + traverse(item)
        return result
    else:
        leaf = tree
        if(type(leaf)==type("")):
            return "STRING:"+leaf
        elif(type(leaf)==type((1,2))):
            if(leaf[0]=="LIST"):
                return "LIST["+traverse(leaf[1])+"]LIST"
            elif(leaf[0]=="NTP"):
                return "NTP("+leaf[1]+","+leaf[2]+")"
            elif(leaf[0]=="COMMENT"):
                return "COMMENT:"+leaf[1]
            else:
                print("UNHANDLED TUPLE"+repr(leaf))
                assert(False)
        else:
            print("UNHANDLED TYPE:"+repr(leaf))
            assert(False)

def parse_execute(s,desiredResult=None):
    global grammar
    print "\nPARSE:",s
    tree = grammar.parseString(s)
    result = traverse(tree.asList())
    print "parse(\""+s+"\")->\""+result+"\""
    if(desiredResult != None):
        print "Got      :",result
        print "Expecting:",desiredResult
        assert(result == desiredResult)

def test():
    define_grammar()
    #spec = open("spec.txt","rt").read()
    parse_execute("name:type","NTP(name,type)")
    parse_execute("name :type","NTP(name,type)")
    parse_execute("name: type","NTP(name,type)")
    parse_execute("name1: typeA","NTP(name1,typeA)")
    parse_execute("name:type # Comment","NTP(name,type)COMMENT: Comment")
    parse_execute("[nameA:typeA,nameB:typeB]","LIST[NTP(nameA,typeA)NTP(nameB,typeB)]LIST")
    parse_execute("[a:b,[c:d,e:f]]","LIST[NTP(a,b)LIST[NTP(c,d)NTP(e,f)]LIST]LIST")
    parse_execute("[]","LIST[]LIST")

    print "\nUnit tests passed OK"
    
if __name__ == "__main__":
    test()
