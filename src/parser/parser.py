from lark import Lark

def parseLogoCode(logoCode):

    with open('logo.lark', encoding='utf-8') as f:
        grammar = f.read()

    parser = Lark(grammar)

    parseTree = parser.parse(logoCode)

    print(parseTree.pretty())

if __name__ == "__main__":
    logoCode = '''
    to main
        fd 100
        lt 90
        sixseven
        pu
        fd 100
        pd
    end

    to sixseven
        repeat 4 [fd 100 rt 90]
    end
    '''

    parseLogoCode(logoCode)