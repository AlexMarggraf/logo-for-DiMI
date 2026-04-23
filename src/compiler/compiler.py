from lark import Lark, Transformer, Visitor

def parseLogoCode(logoCode):

    with open('logo.lark', encoding='utf-8') as f:
        grammar = f.read()

    parser = Lark(grammar)

    logoCode = logoCode.lower()
    parseTree = parser.parse(logoCode)
    return parseTree

# This class is supposed to enforce the semantic of Logo.
class SemanticChecker(Visitor):
    pass

# This class should transform the parseTree into a string of executable python code.
class Compiler(Transformer):
    def STRING(self, token):
        return str(token)
    
    def SIGNED_NUMBER(self, token):
        return int(token)
    
    def identifier(self, items):
        return items[0]
    
    def var_decl(self, items):
        return items[0]
    
    def expr_literal(self, items):
        return items[0]
    
    def make_stmt(self, items):
        return f"{items[0]} = {items[1]}"

if __name__ == "__main__":
    logoCode = '''
    to main
        make "a 100
        fd :a
    end
    '''

    parseTree = parseLogoCode(logoCode)
    print("pretty parsetree:")
    print(f"{parseTree.pretty()} \n")
    print("parse tree in actual form:")
    print(f"{parseTree} \n")
    
    semanticChecker = SemanticChecker()
    semanticTree = semanticChecker.visit(parseTree)

    compiler = Compiler()
    pythonCode = compiler.transform(semanticTree)
    print("first compiler step:")
    print(f"{pythonCode} \n")
    print("resulting pretty parsetree:")
    print(pythonCode.pretty())