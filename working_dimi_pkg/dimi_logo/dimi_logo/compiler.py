from lark import Lark, Transformer
import json
import re
import time
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

def parseLogoCode(logoCode):

    with open(os.path.join(_HERE, 'logo.lark'), encoding='utf-8') as f:
        grammar = f.read()

    parser = Lark(grammar)

    logoCode = logoCode.lower()
    parseTree = parser.parse(logoCode)
    return parseTree

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
        if items[0] == "rand":
            return f"{self.action_set[items[0]]}(1, {items[1]})"

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
        actual = self.action_set["print"]
        output = f"{actual}(\""

        for item in items:
            output += f"{item} "

        output = output[:-1]
        output += "\")"

        return output
    
    def print_exp_stmt(self, items):
        output = f"print("

        for item in items:
            output += f"{item} "

        output = output[:-1]
        output += ")"

        return output
    
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
        make "a (rand 10)
        if((mod :a 2) == 0)[rt 90][lt 90]
    end
    '''

    start = time.time()
    parseTree = parseLogoCode(logoCode)

    print("pretty parsetree:\n")
    print(f"{parseTree.pretty()} \n")

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
