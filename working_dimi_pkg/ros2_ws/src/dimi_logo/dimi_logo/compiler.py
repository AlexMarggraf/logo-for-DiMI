from lark import Lark, Transformer, Visitor
import json
import re
import time
import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

def parseLogoCode(logoCode):

    with open(os.path.join(_HERE, 'logo.lark'), encoding='utf-8') as f:
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

    def __init__(self):
        with open(os.path.join(_HERE, 'action_set.json'), "r") as f:
            self.action_set = json.load(f)

    # Tokens
    def STRING(self, token):
        return str(token)
    
    def SIGNED_NUMBER(self, token):
        s = str(token)

        if "." in s or "e" in s or "E" in s:
            return float(s)
        else:
            return int(s)
        
    def STOP(self, token):
        return "break"

    # Variables and names
    def identifier(self, items):
        return items[0]
    
    def variable(self, items):
        return items[0]
    
    def var_decl(self, items):
        return items[0]
    
    # Colors
    def black(self, _): return f"{self.action_set['color']}(black)"
    def red(self, _): return f"{self.action_set['color']}(red)"
    def green(self, _): return f"{self.action_set['color']}(green)"
    def yellow(self, _): return f"{self.action_set['color']}(yellow)"
    def blue(self, _): return f"{self.action_set['color']}(blue)"
    def magenta(self, _): return f"{self.action_set['color']}(magenta)"
    def cyan(self, _): return f"{self.action_set['color']}(cyan)"
    def white(self, _): return f"{self.action_set['color']}(white)"
    def gray(self, _): return f"{self.action_set['color']}(gray)"
    def grey(self, _): return f"{self.action_set['color']}(grey)"
    def darkred(self, _): return f"{self.action_set['color']}(darkred)"
    def darkgreen(self, _): return f"{self.action_set['color']}(darkgreen)"
    def darkblue(self, _): return f"{self.action_set['color']}(darkblue)"
    def orange(self, _): return f"{self.action_set['color']}(orange)"
    def pink(self, _): return f"{self.action_set['color']}(pink)"
    def purple(self, _): return f"{self.action_set['color']}(purple)"
    def brown(self, _): return f"{self.action_set['color']}(brown)"
    
    # Two argument functions
    def mod(self, _): return "mod"
    def pow(self, _): return "pow"
    
    # One argument functions
    def sin(self, _): return "sin"
    def cos(self, _): return "cos"
    def tan(self, _): return "tan"
    def asin(self, _): return "asin"
    def acos(self, _): return "acos"
    def atan(self, _): return "atan"
    def sqrt(self, _): return "sqrt"
    def rand(self, _): return "rand"
    def round(self, _): return "round"
    def log(self, _): return "log"
    def abs(self, _): return "abs"
    
    # Expressions
    def expr_literal(self, items):
        return items[0]
    
    def expr_in_brackets(self, items):
        return items[0]
    
    def expr_color(self, items):
        return f"{self.action_set['color']}({items[0]}, {items[1]}, {items[2]})"
    
    def expr_unary_arit_op(self, items):
        return f"{items[0]}{items[1]}"
    
    def expr_bin_arit_op(self, items):
        return f"{items[0]} {items[1]} {items[2]}"
    
    def expr_func_two_arg(self, items):
        return f"{self.action_set[items[0]]}({items[1]}, {items[2]})"
    
    def expr_func_one_arg(self, items):
        return f"{self.action_set[items[0]]}({items[1]})"
    
    def expr_func_no_arg(self, items):
        return f"{self.action_set[items[0]]}()"
    
    def expr_const(self, items):
        return self.action_set[items[0]]
    
    def expr_unary_bool_op(self, items):
        return f"{items[0]}{items[1]}"
    
    def expr_bin_bool_op(self, items):
        return f"{items[0]} {items[1]} {items[2]}"

    # Statements
    def make_stmt(self, items):
        return f"{items[0]} = {items[1]}"
    
    def print_str_stmt(self, items):
        output = ""

        for item in items:
            output += f"{item} "

        output = output[:-1]

        return f"print(\"{output}\")"
    
    def print_exp_stmt(self, items):
        output = ""

        for item in items:
            output += f"{item} "

        output = output[:-1]

        return f"print({output})"
    
    def repeat_stmt(self, items):
        body = ""

        for stmt in items[1]:
            body += f"{stmt}\n"

        return f"for i in range({items[0]}):\n__INDENT\n{body}__OVER"
    
    def if_stmt(self, items):
        if_body = "__INDENT\n"

        for stmt in items[1]:
            if_body += f"{stmt}\n"
        
        if_body += "__OVER"

        if len(items) > 2:
            else_body = "else:\n__INDENT\n"

            for stmt in items[2]:
                else_body += f"{stmt}\n"

            else_body += "__OVER"

            return f"if {items[0]}:\n{if_body}\n{else_body}"
        else:
            return f"if {items[0]}:\n{if_body}"
    
    def while_stmt(self, items):
        body = ""

        for stmt in items[1]:
            body += f"{stmt}\n"

        return f"while {items[0]}:\n__INDENT\n{body}__OVER"
    
    def prog_call_stmt(self, items):
        iden = items[0]

        if iden in self.action_set:
            actual = self.action_set[iden]
        else:
            actual = iden

        if actual == "NA":
            return "NA"
        else:
            call = f"{actual}("

            if iden == "wait":
                call += f"{items[1]/100}"
            else:
                for i in range(1, len(items)):
                    call += f"{items[i]}, "
                
                if len(items) > 1:
                    call = call[:-2]

            call += ")"

            return call
    
    def stmt_block(self, items):
        return items
    
    # Program
    def param_list(self, items):
        args = "("

        for item in items:
            args += f"{item}, "
        
        args = args[:-2]
        args += ")"

        return args
    
    def program_declaration(self, items):
        iden = items[0]
        args = ""
        body = ""

        items = [item for item in items if not re.fullmatch(r"\s+", item)]
        
        if(items[1][0] == "("):
            args = items[1]
            
            for i in range(2, len(items)):
                body += f"{items[i]}\n"
        else:
            args = "()"
            for i in range(1, len(items)):
                body += f"{items[i]}\n"
        
        return f"def {iden}{args}:\n__INDENT\n{body}__OVER"

    def prog(self, items):
        program = ""

        items = [item for item in items if not re.fullmatch(r"\s+", item)]
        
        for item in items:
            program += f"{item}\n"

        return program

    def input_lines(self, items):
        program = "def main():\n__INDENT\n"

        items = [item for item in items if not re.fullmatch(r"\s+", item)]
        
        for item in items:
            program += f"{item}\n"

        program += "__OVER"
        return program
    
def indentPythonCode(pythonCode):
    indent = 0
    indentedPythonCode = ""

    lines = pythonCode.split("\n")

    for i in range(len(lines)):
        match_na = re.match(r"NA", lines[i])
        match_indent = re.match(r"__INDENT", lines[i])
        match_indent_over = re.match(r"__OVER", lines[i])

        if match_indent:
            indent += 1
        elif match_indent_over:
            indent -= 1
        elif match_na:
            pass
        else:
            lines[i] = lines[i].replace("NA", "")

            if indent > 0:                
                lines[i] = "\t" * indent + lines[i]
    
            indentedPythonCode += lines[i] + "\n"
    
    return indentedPythonCode + "main()"

def compileLogoCode(logoCode):
    parseTree = parseLogoCode(logoCode)

    compiler = Compiler()
    pythonCode = compiler.transform(parseTree)

    executable = indentPythonCode(pythonCode)
    return executable

if __name__ == "__main__":

    logoCode = '''
    to main
        # Ignore this twin
        print [hello world]
    end
    '''

    logoCode2 = "repeat 4 [fd 100 rt 90]"

    logoCode3 = '''
    to main
        cube
    end

    to cube
        setsc black
        setpw 2
        
        make "a1 100
        make "a2 100
        make "a3 100
        
        make "b1 -100
        make "b2 100
        make "b3 100
        
        make "c1 -100
        make "c2 -100
        make "c3 100
        
        make "d1 100
        make "d2 -100
        make "d3 100
        
        make "e1 100
        make "e2 100
        make "e3 -100
        
        make "f1 -100
        make "f2 100
        make "f3 -100
        
        make "g1 -100
        make "g2 -100
        make "g3 -100
        
        make "h1 100
        make "h2 -100
        make "h3 -100
        
        make "theta1 0.01 * random 600
        make "theta2 0.01 * random 600
        make "theta3 0.01 * random 600

        make "iter 0
        
        while[:iter<1000][
        
        make :theta1 :theta1 + 0.01
        make :theta2 :theta2 + 0.02
        make :theta3 :theta3 + 0.03
        
        make "co1 cos :theta1
        make "co2 cos :theta2
        make "co3 cos :theta3
        
        make "s1 sin :theta1
        make "s2 sin :theta2
        make "s3 sin :theta3
        
        make "ta1 :co3*:co2*:a1 + (:co3*:s2*:s1 - :s3*:co1)*:a2 + (:co3*:s2*:co1 + :s3*:s1)*:a3
        make "ta2 :s3*:co2*:a1 + (:s3*:s2*:s1 + :co3*:co1)*:a2 + (:s3*:s2*:co1 - :co3*:s1)*:a3
        make "ta3 :co2*:s1*:a2 + :co2*:co1*:a3 - :s2*:a1
        
        make "tb1 :co3*:co2*:b1 + (:co3*:s2*:s1 - :s3*:co1)*:b2 + (:co3*:s2*:co1 + :s3*:s1)*:b3
        make "tb2 :s3*:co2*:b1 + (:s3*:s2*:s1 + :co3*:co1)*:b2 + (:s3*:s2*:co1 - :co3*:s1)*:b3 
        make "tb3 :co2*:s1*:b2 + :co2*:co1*:b3 -(:s2*:b1)

        make "tc1 :co3*:co2*:c1 + (:co3*:s2*:s1 - :s3*:co1)*:c2 + (:co3*:s2*:co1 + :s3*:s1)*:c3
        make "tc2 :s3*:co2*:c1 + (:s3*:s2*:s1 + :co3*:co1)*:c2 + (:s3*:s2*:co1 - :co3*:s1)*:c3
        make "tc3 :co2*:s1*:c2 + :co2*:co1*:c3 -(:s2*:c1)

        make "td1 :co3*:co2*:d1 + (:co3*:s2*:s1 - :s3*:co1)*:d2 + (:co3*:s2*:co1 + :s3*:s1)*:d3
        make "td2 :s3*:co2*:d1 + (:s3*:s2*:s1 + :co3*:co1)*:d2 + (:s3*:s2*:co1 - :co3*:s1)*:d3
        make "td3 :co2*:s1*:d2 + :co2*:co1*:d3 -(:s2*:d1)

        make "te1 :co3*:co2*:e1 + (:co3*:s2*:s1 - :s3*:co1)*:e2 + (:co3*:s2*:co1 + :s3*:s1)*:e3
        make "te2 :s3*:co2*:e1 + (:s3*:s2*:s1 + :co3*:co1)*:e2 + (:s3*:s2*:co1 - :co3*:s1)*:e3
        make "te3 :co2*:s1*:e2 + :co2*:co1*:e3 -(:s2*:e1)

        make "tf1 :co3*:co2*:f1 + (:co3*:s2*:s1 - :s3*:co1)*:f2 + (:co3*:s2*:co1 + :s3*:s1)*:f3
        make "tf2 :s3*:co2*:f1 + (:s3*:s2*:s1 + :co3*:co1)*:f2 + (:s3*:s2*:co1 - :co3*:s1)*:f3
        make "tf3 :co2*:s1*:f2 + :co2*:co1*:f3 -(:s2*:f1)

        make "tg1 :co3*:co2*:g1 + (:co3*:s2*:s1 - :s3*:co1)*:g2 + (:co3*:s2*:co1 + :s3*:s1)*:g3
        make "tg2 :s3*:co2*:g1 + (:s3*:s2*:s1 + :co3*:co1)*:g2 + (:s3*:s2*:co1 - :co3*:s1)*:g3
        make "tg3 :co2*:s1*:g2 + :co2*:co1*:g3 -(:s2*:g1)

        make "th1 :co3*:co2*:h1 + (:co3*:s2*:s1 - :s3*:co1)*:h2 + (:co3*:s2*:co1 + :s3*:s1)*:h3
        make "th2 :s3*:co2*:h1 + (:s3*:s2*:s1 + :co3*:co1)*:h2 + (:s3*:s2*:co1 - :co3*:s1)*:h3
        make "th3 + :co2*:s1*:h2 + :co2*:co1*:h3 -(:s2*:h1)
        
        # which face is in front
        make "showa (:ta3 + :tb3 + :tc3 + :td3)/4
        make "showb (:ta3 + :tb3 + :te3 + :tf3)/4
        make "showc (:tc3 + :tb3 + :tf3 + :tg3)/4
        make "showd (:tc3 + :td3 + :tg3 + :th3)/4
        make "showe (:ta3 + :td3 + :th3 + :te3)/4
        make "showf (:te3 + :tf3 + :tg3 + :th3)/4
        
        make "focal 600
        make "offset -700
        
        make "pa1 (:ta1 * :focal) / (:ta3 + :offset)
        make "pa2 (:ta2 * :focal) / (:ta3 + :offset)
        
        make "pb1 (:tb1 * :focal) / (:tb3 + :offset)
        make "pb2 (:tb2 * :focal) / (:tb3 + :offset)
        
        make "pc1 (:tc1 * :focal) / (:tc3 + :offset)
        make "pc2 (:tc2 * :focal) / (:tc3 + :offset)
        
        make "pd1 (:td1 * :focal) / (:td3 + :offset)
        make "pd2 (:td2 * :focal) / (:td3 + :offset)
        
        make "pe1 (:te1 * :focal) / (:te3 + :offset)
        make "pe2 (:te2 * :focal) / (:te3 + :offset)
        
        make "pf1 (:tf1 * :focal) / (:tf3 + :offset)
        make "pf2 (:tf2 * :focal) / (:tf3 + :offset)
        
        make "pg1 (:tg1 * :focal) / (:tg3 + :offset)
        make "pg2 (:tg2 * :focal) / (:tg3 + :offset)
        
        make "ph1 (:th1 * :focal) / (:th3 + :offset)
        make "ph2 (:th2 * :focal) / (:th3 + :offset)

        make "filter 15
        
        #draw sides
        if(:showa > :filter)[setpc 1 surface :pa1 :pa2 :pb1 :pb2 :pc1 :pc2 :pd1 :pd2]
        if(:showb > :filter)[setpc 2 surface :pa1 :pa2 :pb1 :pb2 :pf1 :pf2 :pe1 :pe2]
        if(:showc > :filter)[setpc 3 surface :pb1 :pb2 :pc1 :pc2 :pg1 :pg2 :pf1 :pf2]
        if(:showd > :filter)[setpc 4 surface :pc1 :pc2 :pd1 :pd2 :ph1 :ph2 :pg1 :pg2]
        if(:showe > :filter)[setpc 5 surface :pd1 :pd2 :pa1 :pa2 :pe1 :pe2 :ph1 :ph2]
        if(:showf > :filter)[setpc 6 surface :pe1 :pe2 :pf1 :pf2 :pg1 :pg2 :ph1 :ph2]
        
        make :iter :iter + 1
        wait 1
        wash
        ]
    
    end

    to surface :x1 :y1 :x2 :y2 :x3 :y3 :x4 :y4
        home
        tri :x1 :y1 :x2 :y2 :x3 :y3
        home
        tri :x1 :y1 :x3 :y3 :x4 :y4
    end

    to tri :x1 :y1 :x2 :y2 :x3 :y3

        #vectors between points
        make "ix :x2 - :x1
        make "iy :y2 - :y1
        make "jx :x3 - :x2
        make "jy :y3 - :y2
        make "kx :x1 - :x3
        make "ky :y1 - :y3
        
        #length of vectors
        make "il sqrt(power :ix 2 + power :iy 2)
        make "jl sqrt(power :jx 2 + power :jy 2)
        make "kl sqrt(power :kx 2 + power :ky 2)
        
        #angle between vectors
        make "s 180/pi * arccos (:iy) / (:il)
        make "a1 180/pi * arccos (:ix*:jx + :iy*:jy) / ((:il) * (:jl))
        make "a2 180/pi * arccos (:jx*:kx + :jy*:ky) / ((:jl) * (:kl))
        make "a3 180/pi * arccos (:kx*:ix + :ky*:iy) / ((:kl) * (:il))
        
        setxy :x1 :y1
        
        make "dir 1
        if(:x1 > :x2)[make :dir -1]
        turn :dir :s
        
        #figure out if i need to turn left or right
        #pretty stupid and inefficient
        make :theta (pi/180) * (:dir*:a1)
        
        make "tstx :jx*cos(:theta) - :jy*sin(:theta)
        make "tsty :jx*sin(:theta) + :jy*cos(:theta)
        
        make "cross :ix*:tsty - :iy*:tstx
        
        if(abs :cross > 0.1)[make :dir -1*:dir]
        
        # number of lines filling the triangle
        make "segs 20
        make "rat 1 - (1/:segs)
        
        make "epsi :il - :rat*:il
        make "epsj :jl - :rat*:jl
        make "epsk :kl - :rat*:kl
        
        repeat :segs [
            fd :il
            turn :dir :a1
            fd :jl
            turn :dir :a2
            fd :kl
            turn :dir :a3
            make :il :il - :epsi
            make :jl :jl - :epsj
            make :kl :kl - :epsk
            ]
    end

    to turn :dir :angle
        if(:dir == 1)[rt :angle][lt :angle]
    end
    '''

    start = time.time()

    parseTree = parseLogoCode(logoCode)
    print("pretty parsetree:\n")
    print(f"{parseTree.pretty()} \n")
    """ print("parse tree in actual form:")
    print(f"{parseTree} \n") """

    compiler = Compiler()
    pythonCode = compiler.transform(parseTree)
    print("compile step:\n")
    print(f"{pythonCode} \n")

    pythonCode = indentPythonCode(pythonCode)
    end = time.time()

    print("logo code:")
    print(logoCode + "\n")

    print(f"python code: (compile time: {end-start})")
    print(pythonCode)

    """ print("result:\n")
    exec(pythonCode) """

    """ print("pretty compile tree:")
    print(pythonCode.pretty())"""
