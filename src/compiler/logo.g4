// LOGO Grammar for the text editor (procedures)
// 
// Build instructions: This grammar is _not_ integrated into the build process and needs to be
// manually rebuilt after modification

grammar XLogo;

// Parser rules

// This rule is for parsing the Editor
prog: EOL* (programDeclaration (EOL programDeclaration?)*)? '\uFEFF'? EOF;

// This rule is for parsing a input line (not in a program)
inputLines: (stmt | EOL)* EOF;

// To and end are defined token such that they can be used later in code
programDeclaration:
	To Identifier paramList? EOL (stmt* EOL)* End;

paramList: Variable+;

// Statements

stmt:
	makeStmt
	| printStmt
	| repeatStmt
	| ifStmt
	| whileStmt
	| progCallStmt;

stmtBlock: '[' (stmt | EOL)* ']';

repeatStmt: 'repeat' expr stmtBlock;

ifStmt: 'if' expr stmtBlock ( stmtBlock)?;

whileStmt: 'while' '[' expr ']' stmtBlock;

// ---- Special Built ins ----

// Make has special syntax and semantics
makeStmt: Make VarDecl expr | Make Variable expr;

// Print has special syntax
printStmt: Print '[' .*? ']' | Print expr;
// TODO: Better Lexer for string to also match the comment token '#'

// --- Prog call ---

// Call to a built-in or user defined program.
progCallStmt: Identifier expr*;

// Expresisons

// Labeling each expression. This causes ANTLR to generate a function for each of this cases so we can easier detect which case we're in
expr:
	literal # ExprLiteral
	// Color definition using rgb format
	| '{' expr expr expr '}'				# ExprColor
	| '[' expr expr expr ']'				# ExprColor
	| '(' expr ')'							# ExprInBrackets
	| ('+' | '-' | '!') expr				# ExprUnaryOp
	| expr ('*' | '/' | '%') expr			# ExprBOpMult
	| FuncNameTwoArg expr expr				# ExprFuncTwoArg
	| FuncNameOneArg expr					# ExprFuncOneArg
	| FuncNameNoArg							# ExprFuncNoArg
	| expr ('+' | '-') expr					# ExprBOpAdd
	| expr ('<' | '<=' | '>' | '>=') expr	# ExprBOpComp
	| expr ('=' | '!=') expr				# ExprBOpEq
	| expr '&&' expr						# ExprBOpAnd
	| expr '||' expr						# ExprBOpOr;

// Literals
literal: Variable | Number | Colorname | Boolean;

// Lexer Rules

To: 'to';

End: 'end';

// All functions or constants that require no argument. called 'Func' for consitency with the other
// Func tokens
FuncNameNoArg: PiConst | EConst;

// All functions that require one argument
FuncNameOneArg:
	Sin
	| Tan
	| Abs
	| Arccos
	| Arcsin
	| Arctan
	| Cos
	| Sqrt
	| Random
	| Round
	| Log;

// All functions that require two arguments
FuncNameTwoArg: Mod | Power;

Colorname: (
		'black'
		| 'red'
		| 'green'
		| 'yellow'
		| 'blue'
		| 'magenta'
		| 'cyan'
		| 'white'
		| ColornameGray
		| 'light' ColornameGray
		| 'darkred'
		| 'darkgreen'
		| 'darkblue'
		| 'orange'
		| 'pink'
		| 'purple'
		| 'brown'
	);
ColornameGray: ('gray'|'grey');

// Built-in commands names and alternatives
Make: 'make';
Print: 'print' | 'pr';

// Built-in functions
Sin: 'sin';
Sqrt: 'sqrt';
Tan: 'tan';
Abs: 'abs';
Arccos: 'arccos' | 'acos';
Arcsin: 'arcsin' | 'asin';
Arctan: 'arctan' | 'atan';
Cos: 'cos';
Mod: 'mod';
Random: 'random' | 'rand' | 'rnd';
Round: 'round';
Power: 'power' | 'pow';
Log: 'log' | 'log10';

// Const
PiConst: 'pi';
EConst: 'e';

Variable: ':' Identifier;

VarDecl: '"' Identifier;

Number: Decimal | Decimal '.' Decimal;

Boolean: 'false' | 'true';

Identifier: Letter ( Letter | Digit | '_')*;

fragment Letter:
	'A' ..'Z'
	| 'a' ..'z'
	| '$'
	| '£'
	| '?'
	| '@'
	// German special character
	| 'ä'
	| 'Ä'
	| 'ö'
	| 'Ö'
	| 'ü'
	| 'Ü'
	| 'ß'
	// French special character
	| 'À'
	| 'Â'
	| 'Æ'
	| 'Ç'
	| 'È'
	| 'É'
	| 'Ê'
	| 'Ë'
	| 'Î'
	| 'Ï'
	| 'Ô'
	| 'Œ'
	| 'Ù'
	| 'Û'
	| 'à'
	| 'â'
	| 'æ'
	| 'ç'
	| 'è'
	| 'é'
	| 'ê'
	| 'ë'
	| 'î'
	| 'ï'
	| 'ô'
	| 'œ'
	| 'ù'
	| 'û'
	// Lithuanian special characters
	| 'Ą' 
	| 'ą'
	| 'Č'
	| 'č'
	| 'Ę'
	| 'ę'
	| 'Ė'
	| 'ė'
	| 'Į'
	| 'į'
	| 'Š'
	| 'š'
	| 'Ų'
	| 'ų'
	| 'Ū'
	| 'ū'
	| 'Ž'
	| 'ž'
	;

fragment Decimal: '0' | '0' ..'9' Digit*;
fragment Digit: '0' ..'9';

COMMENT: // comments do not produce tokens:
	'#' ~('\n' | '\r')* -> skip;

// Need EOL tokens since programs declarations must have some rules with EOL
EOL: '\uFEFF'? '\r'? '\n';

// White spaces do not produce tokens:
WS: (' ' | '\t')+ -> skip;
// could also send to Hiddden chanel using '-> channel(HIDDEN)' if is needed later

// handle characters which failed to match any other token
ErrorCharacter: .;