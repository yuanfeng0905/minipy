from context import *
from parse import *
import sys
# this file is auto-generated by gen_tm2c.py

def visitArg(item, context):
    ref = item.first.val
    context.push(ref, sformat("Object %s=argTakeObj(\"test\");", ref));
def visitAssignment(item, context):
    # tempSize = context.getTempSize()
    
    first = item.first
    second = item.second
    if istype(first, 'list'):
        # multiple assignment
        assert len(first) == len(second)
        for i in range(len(first)):
            node = AstNode('=')
            node.first = first[i]
            node.second = second[i]
            visitAssignment(node, context)
    elif first.type == "name":
        visitItem(item.second, context)
        name = first.val
        # ref, val = context.pop()
        # context.push(name, sformat("%s=%s", name, val))
        context.store(name)
        # context.restoreTempSize(tempSize)
    else:
        # handle set, multi-assignment, etc.
        pass

def visitCall(item, context):
    first = item.first
    second = item.second
    visitItem(first, context)
    funcRef, val = context.pop()
    if funcRef == None:
        funcRef = context.getTemp(val)
    if istype(second, "list"):
        argList = []
        for item in second:
            visitItem(item, context)
            ref, val = context.pop()
            if ref == None:
                ref = context.getTemp(val)
            argList.append(ref)
        context.push(None, sformat("tmCall(%s,%s,%s,%s);", \
            getLineNo(item), funcRef, len(argList), ",".join(argList)))
    elif second == None:
        context.push(None, sformat("tmCall(%s,%s,0);", getLineNo(item), funcRef))
    else:
        visitItem(second, context)
        ref, val = context.pop()
        if ref == None:
            ref = context.getTemp(val)
        context.push(None, sformat("tmCall(%s,%s,1,%s);", getLineNo(item), funcRef, ref))



def visitDef(item, context):

    context.push ("##", "#func")
    originName = item.first.val
    # visitItem(item.first, context)
    name = context.getVar(originName)
    # ref, name = context.pop()
    context.push(None, "Object " + name + "() {")
    context.switchToScope("local")
    visitItem(item.second, context)
    visitItem(item.third, context)
    context.push(None, "}\n")
    context.switchToScope("global")
    
    code = context.pop()

    functionCode = []

    while not (code[0] == "##" and code[1] == "#func"):
        functionCode.append(code)
        code = context.pop()
    functionCode.reverse()
    context.defineFunction(originName, functionCode)
    context.push(None, sformat("defFunc(%s, %s, %s);",
        context.getGlobals(), context.getString(originName), name))



def visitIf (item, context):
    # { first : condition, second : body, third : rest }
    condition = item.first
    body = item.second
    rest = item.third

    visitItem(condition, context)

    ref, val = context.pop()

    if ref == None:
        ref = context.getTemp(val)

    context.push (None, sformat("if (isTrue(%s)) { ", ref))

    visitItem(body, context)

    context.push (None, "}")

    if rest != None:
        context.push(None, "else { ")
        visitItem(rest, context)
        context.push(None, "}")



def visitName(item, context):
    if context.scope == "global":
        # ref = context.getVar(item.val)
        context.push(None, sformat("tmGetGlobal(%s, %s)", context.getGlobals(), context.getString(item.val)))
    else:
        context.push(item.val, item.val)

def visitOp(item, context, op):
    visitItem(item.first, context)
    visitItem(item.second, context)
    name2, v2 = context.pop()
    name1, v1 = context.pop()
    if name1 == None:
        name1 = context.getTemp(v1)
    if name2 == None:
        name2 = context.getTemp(v2)
    context.push(None, sformat("%s(%s, %s)", op, name1,name2))

def visitAdd(item, context):
    visitOp(item, context, "objAdd")

def visitSub(item, context):
    visitOp(item, context, "objSub")

def visitMul(item, context):
    visitOp(item, context, "objMul")

def visitDiv(item, context):
    visitOp(item, context, "objDiv")

def visitMod(item, context):
    visitOp(item, context, "objMod")

def visitReturn(item, context):
    visitItem(item.first, context)
    ref, val = context.pop()
    context.push(None, "return " + val + ";")


def visitNumber(item, context):
    ref = context.getNumber(item.val)
    context.push(ref, ref)

def visitString(item, context):
    ref = context.getString(item.val)
    context.push(ref, ref)

def visitNone(item, context):
    context.push("NONE_OBJ", "NONE_OBJ")

    


def getLineNo(item):
    if hasattr(item, "pos"):
        return item.pos[0]
    elif hasattr(item, "first"):
        return getLineNo(item.first)


_handlers = {
    "number": visitNumber,
    "name":   visitName,
    "string": visitString,
    "None": visitNone,
    "=" : visitAssignment,
    "+" : visitAdd,
    "if": visitIf,
    "call": visitCall,
    "def": visitDef,
    "arg": visitArg,
    "return": visitReturn
}

def visitItem0(item, context):
    _handlers[item.type](item, context)

def visitItem(item, context):
    context.item = item
    if istype(item, "list"):
        for item0 in item:
            visitItem(item0, context)
    else:
        visitItem0(item, context)

def visitItemList(itemList, context):
    for item in itemList:
        tempSize = context.getTempSize()
        visitItem(item, context)
        context.restoreTempSize(tempSize)


def tm2c(fname, src, prefix=None):
    tree = parse(src)
    # printAst(tree)
    context = Context()
    context.setFname(prefix)
    try:
        visitItemList(tree, context)
    except Exception as e:
        traceback()
        printAst(context.item)
    return context.getCode()
    
if __name__ == "__main__":
    name = sys.argv[1]
    # path = "../test/tm2c/" + name
    path = name
    text = load(path)
    pathes = path.split('/')
    if len(pathes) > 1:
        name = pathes[-1]
    mod = name.split(".")[0]
    code = tm2c(name, text, mod)
    print(code)
