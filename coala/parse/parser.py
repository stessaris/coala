#
# Copyright (c) 2016, Christian Schulz-Hanke
#
import parse_objects as ps
import ply.yacc as yacc
import lexer
import os
		
# Parsing rules

##class Parser(bcParse):
class Parser(object):

	tokens = lexer.Lexer.tokens
	
	#precedence = (
	#	('left','PLUS','MINUS'),
	#	('left','TIMES','DIVIDE'),
	#	('right','UMINUS'),
	#	)
	
	# dictionary of names
	data = { 'actions' : [] ,
	'fluents' : [] ,
	'defined_fluents' : [],
	'preds' : [] ,
	'integers' : [], # Integer facts
	'static_laws' : [] ,
	'dynamic_laws' : [] ,
	'impossible_laws' : [] ,
	'nonexecutable_laws' : [] ,
	'default_laws' : [] ,
	'inertial_laws' : [] ,
	'initially_laws' : [] ,
	'goals' : [],
	'killEncoding' : [],
	'errors' : [],
	'others' : [],
	'roles' : {},
	'visible_laws' : [] }
	lawid = 1
	
	# will be filled with the lines to parse
	my_lines = []
	meta_info = None
	debug = False
	
	start = 'program'
	
	def p_program(self,t):
		'''program :
					| program rule DOT
					| program ESCAPE_ASP
					| program ROLE_BEGIN role ROLE_END'''
		if len(t) == 3:
			self.data['others'].append(ps.asp_code(str(t[2])[5:-6]))
		elif len(t) == 4:
			if not t[2] is None:
				self.data[t[2].get_law_type()].append(t[2])
		elif len(t) == 5: 
			name = str(t[2])[5:-1].lstrip()
			index = name.find("(")
			end_ind = name.find(")")
			params = []
			if index > 0 and end_ind > index:
				name_real = name[:index]
				subs = name[index+1:end_ind]
				index = subs.find(",")
				while index >= 0:
					params.append(subs[:index])
					subs = subs[index+1:]
					index = subs.find(",")
				params.append(subs)
				t[3]['params'] = params
				name = name_real
			self.data['roles'][name]=t[3]
	
	def p_role(self,t):
		'''role :
				| role rule DOT
				| role ESCAPE_ASP'''
		if len(t) == 1:
			t[0] = { 'actions' : [] ,
				'fluents' : [] ,
				'defined_fluents' : [],
				'preds' : [] ,
				'int' : [], # Integer facts
				'static_laws' : [] ,
				'dynamic_laws' : [] ,
				'impossible_laws' : [] ,
				'nonexecutable_laws' : [] ,
				'default_laws' : [] ,
				'inertial_laws' : [] ,
				'initially_laws' : [] ,
				'goals' : [],
				'killEncoding' : [0,0],
				'others' : [],
				'visible_laws' : [],
				'params' : [] }
		if len(t) == 3:
			t[0] = t[1]
			t[0]['others'].append(ps.asp_code(str(t[2])[5:-6]))
		elif len(t) == 4:
			t[0] = t[1]
			t[0][t[2].get_law_type()].append(t[2])
	
	def p_rule(self,t):
		'''rule : fact 
				| law 
				| query '''
		t[0] = t[1]
	
	def p_fact(self,t):
		''' fact : pred_fact
				| act_fact 
				| flu_fact '''
		#		| int_fact
		t[0] = t[1]		

	def p_law(self,t):
		''' law : static_law 
				| dynamic_law 
				| inertial_law 
				| default_law
				| imposs_law
				| nonexe_law 
				| visible_law'''
		t[0] = t[1]
	
	def p_visible_law(self,t):
		''' visible_law : VISIBLE fluent_formula if_part where_part '''
#				| VISIBLE fluent_formula after_part where_part '''
		# TODO: is t[2], t[3] or t[4] false? Then ignore this law!
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.visible_law(t[2],t[3],t[4],line=line,filename=filename)			
	
		
	def p_query(self,t):
		''' query : init_rule 
				| goal_query '''
		t[0] = t[1]
		
	def p_pred_fact(self,t): # <action> a_1,...,a_n <where> bla.
		''' pred_fact : formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.predicate_fact(t[1],t[2],line=line,filename=filename)
		
	def p_act_fact(self,t): # <action> a_1,...,a_n <where> bla.
		''' act_fact :  ACT fluent_formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.action_fact(t[2],t[3],line=line,filename=filename)
		
# 	def p_int_fact(self,t): # <action> a_1,...,a_n <where> bla.
# 		''' int_fact :  INT fluent_formula int_domain where_part'''
# 		line,filename=self.get_meta(t.lineno(1))
# 		t[0] = ps.integer_fact(t[2],t[3],t[4],line=line,filename=filename)
		
	def p_flu_fact(self,t): # <fluent> f_1,...,f_n <where> bla.
		''' flu_fact : FLU fluent_formula where_part
					| DFLU fluent_formula where_part
					| FLU fluent_formula int_domain where_part
					| DFLU fluent_formula int_domain where_part
					| FLU fluent EQ LBRAC term COMMA term_list RBRAC where_part
					| DFLU fluent EQ LBRAC term COMMA term_list RBRAC where_part
					| INT fluent_formula where_part '''		
#					| FLU fluent_list EQ LBRAC term COMMA term_list RBRAC where_part
#					| DFLU fluent_list EQ LBRAC term COMMA term_list RBRAC where_part
		line,filename=self.get_meta(t.lineno(1))
		if len(t) == 4:
			if t[1] == '<int>':
				t[0] = ps.integer_fact(t[2],None,t[4],line=line,filename=filename)
			elif t[1] not in ['<fluent>','fluent']:
				t[0] = ps.defined_fluent_fact(t[2],t[3],line=line,filename=filename)
			else:
				t[0] = ps.fluent_fact(t[2],t[3],line=line,filename=filename)
		elif len(t) == 10:
			termlist = t[7]
			termlist.combine(t[5],reverse=True)
			if t[1] not in ['<fluent>','fluent']:
				t[0] = ps.defined_fluent_fact(ps.atom_list(t[2]),t[9],multivalued=termlist,line=line,filename=filename)
			else:
				t[0] = ps.fluent_fact(ps.atom_list(t[2]),t[9],multivalued=termlist,line=line,filename=filename)
		else:
			#if t[1] not in ['<fluent>','fluent']:
			#	t[0] = ps.integer_fact(t[2],t[3],t[4],line=line,filename=filename)
			#else:
				t[0] = ps.integer_fact(t[2],t[3],t[4],line=line,filename=filename)
		
	def p_static_law(self,t): # f_1,...,f_n <if> g_1,...,g_m <where> bla.
		''' static_law : formula IF formula ifcons_part where_part
						| formula IFCONS formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		if len(t) == 6:
			head = t[1]; ifpart = t[3]; ifcons = t[4]; wherepart = t[5]
		else:
			head = t[1]; ifpart = None; ifcons = t[3]; wherepart = t[4]
		if head.is_false():
			t[0] = ps.impossible_law(ifpart,ifcons,wherepart,line=line,filename=filename)
		elif len(head) > 0:
			t[0] = ps.static_law(head,ifpart,ifcons,wherepart,line=line,filename=filename)

	def p_dynamic_law(self,t): # a <causes> f_1,...,f_n <if> g_1,...,g_m <where> bla.
		''' dynamic_law : formula after_part ifcons_part where_part
					| formula CAUSES formula where_part
					| formula CAUSES formula IF formula where_part'''
#		 ''' dynamic_law : formula after_part ifcons_part where_part
#					 | formula CAUSES formula where_part
#					 | formula CAUSES formula IF formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		if t[2] in ['<causes>','causes']:
			if len(t) == 5: 
				head = t[3]; after = t[1]; ifcons = None; where = t[4];
			else: 
				head = t[3]; t[1].combine(t[5]); after = t[1]; ifcons = None; where = t[6];
		else:
			head = t[1]; after = t[2]; ifcons = t[3]; where = t[4]
		if head.is_false():
			t[0] = ps.nonexecutable_law(after,ifcons,where,line,filename)
		elif len(head) > 0:
			t[0] = ps.dynamic_law(head,after,ifcons,where,line,filename)
					
		
	def p_inertial_law(self,t):
		''' inertial_law : INERTIAL fluent_formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.inertial_law(t[2],t[3],line,filename)
		
	def p_default_law(self,t):
		''' default_law : DEFAULT formula where_part
					| DEFAULT formula IF formula where_part
					| DEFAULT formula AFTER formula where_part''' #TODO: default ifcons??
		line,filename=self.get_meta(t.lineno(1))
		if len(t) == 4: 
			head = t[2]; ifpart = None; after = None; where = t[3]
		elif t[3] in ['<if>','if']:
			head = t[2]; ifpart = t[4]; after = None; where = t[5]
		else:	
			head = t[2]; ifpart = None; after = t[4]; where = t[5]
		t[0] = ps.default_law(head,ifpart,after,where,line,filename)
		
	def p_imposs_law(self,t):
		''' imposs_law : IMPOSSIBLE formula ifcons_part where_part'''
		line,filename=self.get_meta(t.lineno(1))
		if t[2].is_false():
			t[0] = None
		elif (t[2] is None or len(t[2]) == 0) and ( t[3] is None or len(t[3]) == 0):
			t[0] = ps.kill_encoding()
		else:
			t[0] = ps.impossible_law(t[2],t[3],t[4],line,filename)
		#TODO: Kill encoding if formula is true or empty.
		#self.data['killEncoding'][0] = 1
		#TODO: Ignore if false in t[2]
		
		
	def p_nonexe_law(self,t): # NONEXECUTABLE <impossible> a_1,..., a_n <if> f_1,..., f_m <where> bla.	=	<caused> <false> <after> a_1,...,a_n,f_1,...,f_m <where> bla.
		''' nonexe_law : NONEXE formula if_part ifcons_part where_part'''
		line,filename=self.get_meta(t.lineno(1))
		if t[2].is_false():
			t[0] = None
		if (t[2] is None or len(t[2]) == 0) and (t[3] is None or len(t[3]) == 0) \
			and (t[4] is None or len(t[4]) == 0):
			t[0] = ps.kill_encoding(dynamic=True)
		else:
			t[0] = ps.nonexecutable_law(t[2],t[3],t[4],t[5],line,filename)
		#TODO: Kill encoding if formula is true or empty.
		#self.data['killEncoding'][1] = 1
		#TODO: Ignore if false in t[2]
			
##########################
	
	def p_init_rule(self,t): # <initially> f_1,..., f_n <where> bla.	=	f_1,...,f_n <holds at> 0 <where> bla.
		''' init_rule : INIT formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.initial_law(t[2],t[3],line,filename)
		#TODO: Ignore if empty.
		
	def p_goal_query(self,t): # <goal> f_1,...,f_n <where> bla.
		''' goal_query : GOAL formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.goal_law(t[2],t[3],line,filename)
		#TODO: Ignore if empty.
		
##########################

	def p_if_part(self,t):
		''' if_part : 
					| IF formula '''
		if len(t) == 3:
			if t[2].is_false(): t[0] = t[2]
			elif len(t[2]) == 0: t[0] = None #TODO: is this required?
			else: t[0] = t[2]
		else: t[0] = None

	def p_after_part(self,t):
		''' after_part : AFTER formula '''
		if t[2].is_false(): t[0] = t[2]
		elif len(t[2]) == 0: t[0] = None #TODO: is this required?
		else: t[0] = t[2]

	def p_ifcons_part(self,t):
		''' ifcons_part : 
					| IFCONS formula '''
		if len(t) == 3: 
			if t[2].is_false(): t[0] = t[2]
			elif len(t[2]) == 0: t[0] = None #TODO: is this required?
			else: t[0] = t[2]
		else: t[0] = None

	def p_where_part(self,t):
		''' where_part : 
					| WHERE bindings '''
		if len(t) == 3: t[0] = t[2]
		else: t[0] = None #[]
		
	def p_bindings(self,t):
		''' bindings : binding
					| bindings COMMA binding'''
		if len(t) == 2: 
			t[0] = ps.atom_list(t[1])
		else: 
			t[1].combine(t[3])
			t[0] = t[1]
		
	def p_binding(self,t):
		''' binding : ACT fluent
					| FLU fluent equalpart
					| NOT asp_term
					| asp_term '''
####		#			| MINUS fluent'''
		#			| MINUS asp_term # Some things should not happen - 1==1
		if len(t) == 2: 
			t[0] = t[1] #ps.predicate(t[1],None)
		elif t[1] in ['<action>','action']:
			t[0] = ps.action(t[2])
		elif t[1] in ('not','-'):
			t[0] = ps.negation(t[2]) #ps.predicate(ps.negation(t[2]))
		else:
			t[0] = ps.fluent(t[2],t[3])
			
##########################

	def p_formula(self,t): # f_1,...,f_n
		''' formula : tfa 
					| formula COMMA tfa '''
		if len(t) == 4: 
			if t[3].is_false(): # Something and False is always false
				t[0] = t[3]
			else:
				t[1].combine(t[3])
				t[0] = t[1]
		else:
			t[0] = t[1]
		
	def p_tfa(self,t):
		##''' tfa : atom 
		''' tfa : asp_term
				| NOT fluent equalpart
				| TRUE 
				| FALSE '''
		#		| MINUS fluent EQ term
		#		| MINUS fluent equalpart
		if len(t) == 4:
			if t[3] is not None:
				t[0] = ps.atom_list(ps.negation(ps.equation(t[2],t[3])))
			else:
				t[0] = ps.atom_list(ps.negation(t[2]))
		elif len(t) == 5:
			t[0] = ps.atom_list(ps.negation(ps.equation(t[2],t[4])))
		elif t[1] == '<true>': # in ['<true>','true']: 
			#t[0] = [] # True does not lead to anything... t[0] = t[1]
			t[0] = ps.atom_list()
		elif t[1] == "<false>": #in ['<false>','true']: 
			t[0] = ps.false_atom() # Something and False is always false
		else:
			t[0] = ps.atom_list(t[1])
			
#TODO: String action instead of "<action>" : if x in ["action","<action>"]

# 	def p_fluent_list(self,t):
# 		''' fluent_list : fluent
# 					| fluent_list COMMA fluent '''
# 		if len(t) == 2:
# 			t[0] = ps.atom_list(t[1])
# 		else:
# 			t[1].append(t[3])
# 			t[0] = t[1]

	def p_fluent_formula(self,t): # f_1,...,f_n
		''' fluent_formula : fluent equalpart
					| fluent_formula COMMA fluent equalpart '''
		if len(t) == 5: 
			if t[4] == None: 
				t[1].append(t[3])
				t[0] = t[1]
			else: 
				t[1].append(ps.equation(t[3],t[4]))
				t[0] = t[1]
		else: 
			if t[2] == None: 
				t[0] = ps.atom_list(t[1])
			else: 
				t[0] = ps.atom_list(ps.equation(t[1],t[2]))
		
	def p_equalpart(self,t):
		''' equalpart : 
					| EQ term'''
		if len(t) == 3: 
			t[0] = t[2]
		else: 
			t[0] = None
		
	def p_fluent(self,t):
		''' fluent : identifier 
					| var_term
					| IDENTIFIER LBRAC term_list RBRAC '''
		if len(t) == 2: 
			t[0] = t[1]
		else: 
			t[0] = ps.predicate(t[1],t[3])
		
	def p_term_list(self,t):
		''' term_list : term
					| term COMMA term_list '''
		if len(t) == 2: 
			t[0] = ps.atom_list(t[1])
		else: 
			t[3].combine(t[1],reverse=True)
			t[0] = t[3]
			
	def p_term_or_negated_ident(self,t):
		''' term_or_negated_ident : MINUS identifier
					| term '''
		if len(t) == 2:
			t[0] = t[1]
		else:
			t[0] = ps.operation("-1",t[2],operator="*") #ps.negation(t[2])
			
	def p_term(self,t): # X, a, 3, X;Y, 1..Z
		''' term : var_term 
					| identifier 
					| NUMBER 
					| IDENTIFIER LBRAC term_list RBRAC '''
		#			| MINUS NUMBER 
		if len(t) == 2: 
			t[0] = t[1]
		#elif len(t) == 3: 
		#	t[0] = t[1]+t[2]
		else:
			t[0] = ps.predicate(t[1],t[3]) 
		
	def p_var_term(self,t):
		''' var_term : VARIABLE '''
		t[0] = ps.variable(t[1])
		
	def p_identifier(self,t):
		''' identifier : IDENTIFIER '''
		t[0] = ps.unknown(t[1])
		
	def p_int_domain(self,t):
		''' int_domain : COLON term DDOT term 
				| COLON INT '''
		#''' int_domain : 
		#		| COLON term DDOT term 
		#		| COLON INT '''
		#		| COLON term
		#if len(t) == 3:
		#	t[0] = t[2]
		#el
		if len(t) == 5:
			t[0] = ps.atom_list(t[2],t[4])
		elif len(t) == 3:
			t[0] = None
		else: 
			t[0] = None
		
#################
#expr --> expr + term | term
#term --> term * factor | factor
#factor --> ( expr ) | number
#number --> number digit | digit
#digit --> 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9	
#################

	def p_asp_term(self,t):
		#''' asp_term : asp_operation
		''' asp_term : term
					| MINUS term
					| term ASSIGN asp_operation
					| asp_operation asp_eqoperator asp_operation'''
		if len(t) == 4:
			if t[2] == ":=":
				t[0] = ps.assignment(t[1],t[3])
			else:
				t[0] = ps.equation(t[1],t[3],operator=t[2])
		elif len(t) == 3:
			t[0] = ps.negation(t[2])
		else:
			t[0] = t[1]
			
	def p_asp_eqoperator(self,t):
		''' asp_eqoperator : EQQ
							| EQ
							| NEQ 
							| LT 
							| GT 
							| LE 
							| GE '''
		t[0] = t[1]

	def p_asp_operation(self,t):
		''' asp_operation : asp_mult_operation
						| asp_operation PLUS asp_mult_operation
						| asp_operation MINUS asp_mult_operation '''
		if len(t) == 2:
			t[0] = t[1]
		else: 
			t[0] = ps.operation(t[1],t[3],operator=t[2])
			
	def p_asp_mult_operation(self,t):
		''' asp_mult_operation : asp_pow_operation
						| asp_mult_operation TIMES asp_pow_operation
						| asp_mult_operation DIV asp_pow_operation '''
		if len(t) == 2:
			t[0] = t[1]
		else: 
			t[0] = ps.operation(t[1],t[3],operator=t[2])
			
	def p_asp_pow_operation(self,t):
		''' asp_pow_operation : asp_brac_operation
						| asp_pow_operation POWER asp_brac_operation '''
		if len(t) == 2:
			t[0] = t[1]
		else: 
			t[0] = ps.operation(t[1],t[3],operator=t[2])
			
	def p_asp_brac_operation(self,t):
		''' asp_brac_operation : term_or_negated_ident
						| LBRAC asp_operation RBRAC '''
		#''' asp_brac_operation : term
		#				| LBRAC asp_operation RBRAC '''
		if len(t) == 2:
			t[0] = t[1]
		else: 
			t[0] = t[2]
				

#################

	def p_error(self,t):
		if t is not None:
			if len(self.my_lines) >= t.lineno:
				if not self.meta_info is None:
					r = None
					f = 0
					for y in self.meta_info:
						if y[0] < t.lineno and y[1]+y[0] >= t.lineno-1:
							r = y[-1]
							f = y[0]
							break
					if not r is None:
						erro = "ERROR: "+str(r)+" Line "+str(t.lineno-f)+": '"+self.my_lines[t.lineno-1]+"'\n\tSyntax error at Token '"+str(t.value)+"'"
					else:
						erro = "ERROR: Line "+str(t.lineno)+": '"+self.my_lines[t.lineno-1]+"'\n\tSyntax error at Token '"+str(t.value)+"'"
				else:
					erro = "ERROR: Line "+str(t.lineno)+": '"+self.my_lines[t.lineno-1]+"'\n\tSyntax error at Token '"+str(t.value)+"'"
			else:
				erro = "ERROR: Line "+str(t.lineno)+": Syntax error at Token '"+str(t.value)+"'"
		else:
			erro = "ERROR: Unexpected end of input."
		#print "% Line "+str(t.lineno)+": Syntax error at Token '"+str(t.value)+"'"
		self.data['errors'].append(erro)
		
	def get_meta(self,lineno):
		filename = ""
		my_lineno = lineno
		if not self.meta_info is None:
			for x in self.meta_info:
				#y = self.meta_info[x]
				if x[0] < lineno and x[1]+x[0] >= lineno:
					filename = x[2]
					my_lineno = lineno-x[0]
					break
		return my_lineno, filename
		

	#def build(self,alexer,**kwargs):
	def build(self,**kwargs):
		#print self.tokens
		mypath = os.path.dirname(os.path.realpath(__file__))
		self.reset_data()
		
		#self.parser = yacc.yacc(module=self, debug=True, outputdir=mypath, **kwargs) #TODO: remove
		#return
		
		if self.debug:
			self.parser = yacc.yacc(module=self, debug=False, outputdir=mypath, **kwargs) # SILENT MODE!
		else:
			self.parser = yacc.yacc(module=self, debug=False, optimize=False, outputdir=mypath, write_tables=False, **kwargs) # SILENT MODE!
		#self.parser = yacc.yacc(module=self, **kwargs)
		
	def reset_data(self):
		self.data = { 'actions' : [] ,
		'fluents' : [] ,
		'defined_fluents' : [],
		'preds' : [] ,
		'integers' : [], # Integer facts
		'static_laws' : [] ,
		'dynamic_laws' : [] ,
		'impossible_laws' : [] ,
		'nonexecutable_laws' : [] ,
		'default_laws' : [] ,
		'inertial_laws' : [] ,
		'initially_laws' : [] ,
		'goals' : [],
		'killEncoding' : [],
		'errors' : [],
		'others' : [],
		'roles' : {},
		'visible_laws' : [] }
		self.lawid = 1
		self.my_lines = []
		self.meta_info = None
		
	def submit_text(self,text,meta):
		self.my_lines = text.split("\n")
		self.meta_info = meta 
		
	def debug_output(self):
		
		print "-------------------"
		
		print "ASP Stuff: ","; ".join(str(x) for x in self.data['preds'])
		print "Actions: ","; ".join(str(x) for x in self.data['actions'])
		print "Fluents: ","; ".join(str(x) for x in self.data['fluents'])
		print "Integers: ","; ".join(str(x) for x in self.data['integers'])
		print "defined_fluents: ","; ".join(str(x) for x in self.data['defined_fluents'])
		print "static_laws: ","; ".join(str(x) for x in self.data['static_laws'])
		print "dynamic_laws: ","; ".join(str(x) for x in self.data['dynamic_laws'])
		print "impossible_laws: ","; ".join(str(x) for x in self.data['impossible_laws'])
		print "default_laws: ","; ".join(str(x) for x in self.data['default_laws'])
		print "nonexecutable_laws: ","; ".join(str(x) for x in self.data['nonexecutable_laws'])
		print "inertial_laws: ","; ".join(str(x) for x in self.data['inertial_laws'])
		print "initially_laws: ","; ".join(str(x) for x in self.data['initially_laws'])
		print "goals: ","; ".join(str(x) for x in self.data['goals'])
		print "roles: ","; ".join(str(x) for x in self.data['roles'])
		
		if True:
			
			print "-------------------"
			
			print "ASP Stuff: ","; ".join(x.typestr() for x in self.data['preds'])
			print "Actions: ","; ".join(x.typestr() for x in self.data['actions'])
			print "Fluents: ","; ".join(x.typestr() for x in self.data['fluents'])
			print "Integers: ","; ".join(x.typestr() for x in self.data['integers'])
			print "defined_fluents: ","; ".join(x.typestr() for x in self.data['defined_fluents'])
			print "static_laws: ","; ".join(x.typestr() for x in self.data['static_laws'])
			print "dynamic_laws: ","; ".join(x.typestr() for x in self.data['dynamic_laws'])
			print "impossible_laws: ","; ".join(x.typestr() for x in self.data['impossible_laws'])
			print "default_laws: ","; ".join(x.typestr() for x in self.data['default_laws'])
			print "nonexecutable_laws: ","; ".join(x.typestr() for x in self.data['nonexecutable_laws'])
			print "inertial_laws: ","; ".join(x.typestr() for x in self.data['inertial_laws'])
			print "initially_laws: ","; ".join(x.typestr() for x in self.data['initially_laws'])
			print "goals: ","; ".join(x.typestr() for x in self.data['goals'])
			#print "roles: ","; ".join(x.typestr() for x in self.data['roles'])
			print "roles: ","; ".join(str(x) for x in self.data['roles'])
		
		print "-------------------"