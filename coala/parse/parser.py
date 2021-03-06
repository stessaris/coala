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
		''' program : program_part
					| program program_part'''
		pass
	
	def p_program_part(self,t):
		'''program_part : rule DOT
					| ESCAPE_ASP
					| ROLE_BEGIN role ROLE_END'''
		if len(t) == 2:
			self.data['others'].append(ps.asp_code(str(t[1])[5:-6]))
		elif len(t) == 3:
			if not t[1] is None:
				if type(t[1])==list or type(t[1])==ps.atom_list:
					for x in t[1]:
						self.data[x.get_law_type()].append(x)
				else:
					self.data[t[1].get_law_type()].append(t[1])
		elif len(t) == 4: 
			name = str(t[1])[5:-1].lstrip()
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
				t[2]['params'] = params
				name = name_real
			self.data['roles'][name]=t[2]
	
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
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.visible_law(t[2],t[3],t[4],line=line,filename=filename)			
	
		
	def p_query(self,t):
		''' query : init_rule 
				| goal_query '''
		t[0] = t[1]
		
	def p_pred_fact(self,t): # <action> a_1,...,a_n <where> bla.
#		''' pred_fact : formula where_part'''
		''' pred_fact : formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.predicate_fact(t[1],t[2],line=line,filename=filename)
		
	def p_act_fact(self,t): # <action> a_1,...,a_n <where> bla.
		''' act_fact :  ACT fluent_formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.action_fact(t[2],t[3],line=line,filename=filename)
		
	def p_flu_fact(self,t): # <fluent> f_1,...,f_n <where> bla.
		''' flu_fact : FLU fluent_formula where_part
					| INT fluent_formula where_part
					| defined_fluent fluent_formula where_part '''		
		line,filename=self.get_meta(t.lineno(1))
		if t[1] == '<int>':
			stuff = []
			if type(t[2]) == ps.atom_list:
				for x in t[2]:
					if type(x) == ps.fluent_multival:
						if type(x.multidomain) == list:
							int_dom = ps.atom_list(x.multidomain)
						else:
							int_dom = x.multidomain
						
						#stuff.append(x.content)
						stuff.append(ps.integer_fact(ps.atom_list(x.content),int_dom,t[3],line=line,filename=filename))
					else:
						stuff.append(ps.integer_fact(ps.atom_list(x),None,t[3],line=line,filename=filename))
				#t[0] = ps.integer_fact(ps.atom_list(stuff),None,t[3],line=line,filename=filename)
				t[0] = ps.atom_list(stuff)
			else:
				t[0] = ps.integer_fact(ps.atom_list(t[2]),None,t[3],line=line,filename=filename)
		elif t[1] not in ['<fluent>','fluent']:
			t[0] = ps.defined_fluent_fact(t[2],t[3],line=line,filename=filename)
		else:
			
			if type(t[2]) == ps.atom_list: # Get integer fluent declarations
				result = []
				previous = []
				t[2].get_children().reverse() # Reverse order that we get them as expected
				for x in t[2]: # accumulate facts until there is a domain statement
					if type(x) == ps.fluent_multival:
						domain = x.multidomain
						if x.is_int:
							if type(x.multidomain) == list:
								domain = ps.atom_list(x.multidomain)
							elif type(x.multidomain) == ps.value_range and len(x.multidomain.content) == 2:
								lower = x.multidomain.content[0]
								upper = x.multidomain.content[1]
								domain = ps.atom_list(lower,upper)
							else:
								domain = x.multidomain
							
							result.append(ps.integer_fact(ps.atom_list(previous+[ps.unknown(x.content)]),domain,t[3],line=line,filename=filename))
						else:
							if type(x.multidomain) == ps.value_range and len(x.multidomain.content) == 2:
								lower = x.multidomain.content[0] #clingo 5..10 domain statement
								upper = x.multidomain.content[1]
								dotted_domain=(lower,upper)
								for y in previous:
									y.dotted_domain = dotted_domain
								result.append(ps.fluent_fact(ps.atom_list(previous+[x]),t[3],dotted_domain=dotted_domain,line=line,filename=filename))
							else:
								for y in previous:
									y.multidomain = domain
								result.append(ps.fluent_fact(ps.atom_list(previous+[x]),t[3],multivalued=domain,line=line,filename=filename))
							#add list for this domain.
						previous = []
					else:
						previous.append(x)
				result.append(ps.fluent_fact(ps.atom_list(previous),t[3],line=line,filename=filename))
				t[0] = ps.atom_list(result)
			
# 			if type(t[2]) == ps.atom_list: # Get integer fluent declarations
# 				others = []
# 				regular = []
# 				for x in t[2]: # This happens if integer and non_integers are mixed in one declaration.
# 					if type(x) == ps.fluent_multival:
# 						if type(x.multidomain) == list:
# 							if x.is_int:
# 								others.append(ps.integer_fact(ps.atom_list(x.content),ps.atom_list(x.multidomain),t[3],line=line,filename=filename))
# 							else:
# 								regular.append(ps.fluent_fact(ps.atom_list(x),t[3],line=line,filename=filename))						 
# 						elif type(x.multidomain)==ps.value_range and len(x.multidomain.content) == 2:
# 							lower = x.multidomain.content[0]
# 							upper = x.multidomain.content[1]
# 							if x.is_int:
# 								others.append(ps.integer_fact(ps.atom_list(x.content),ps.atom_list(lower,upper),t[3],line=line,filename=filename))
# 							else:
# 								others.append(ps.fluent_fact(ps.atom_list(x),t[3],dotted_domain=(lower,upper),line=line,filename=filename))
# 						else:
# 							regular.append(ps.fluent_fact(ps.atom_list(x),t[3],line=line,filename=filename))
# 					else:
# 						regular.append(ps.fluent_fact(ps.atom_list(x),t[3],line=line,filename=filename))
# 				if len(others) > 0:
# 					if len(regular)+len(others)>1:
# 						if len(others) == 1:
# 							int_dom=others[0].domain
# 							t[0] = ps.integer_fact(t[2],int_dom,t[3],line=line,filename=filename)								
# 						else:
# 							t[0] = ps.atom_list(regular,others)
# 					else:
# 						t[0] = others[0]
# 				else:
# 					t[0] = ps.fluent_fact(t[2],t[3],line=line,filename=filename)
			else:
				#print "Do WE even get here? <-- NO."
				t[0] = ps.fluent_fact(t[2],t[3],line=line,filename=filename)
		
		
	def p_defined_fluent(self,t):
		'''defined_fluent : DFLU
						| DEF FLU'''
		t[0] = "definedfluent"
		
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
		line,filename=self.get_meta(t.lineno(1))
		if t[2] in ['<causes>','causes']:
			if len(t) == 5: 
				head = t[3]; after = t[1]; ifcons = None; where = t[4];
			else: 
				head = t[3]; t[1].combine(t[5]); after = t[1]; ifcons = None; where = t[6];
		else:
			head = t[1]; after = t[2]; ifcons = t[3]; where = t[4]
		if head.is_false():
			t[0] = ps.nonexecutable_law(after,None,ifcons,where,line,filename)
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
		dynamic = None
		if len(t) == 4: 
			head = t[2]; ifpart = None; after = None; where = t[3]
		elif t[3] in ['<if>','if']:
			head = t[2]; ifpart = t[4]; after = None; where = t[5]
			dynamic = False
		else:	
			head = t[2]; ifpart = None; after = t[4]; where = t[5]
			dynamic = True
		t[0] = ps.default_law(head,ifpart,after,where,dynamic,line,filename)
		
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
		
	def p_goal_query(self,t): # <finally> f_1,...,f_n <where> bla.
		''' goal_query : GOAL formula where_part'''
		line,filename=self.get_meta(t.lineno(1))
		t[0] = ps.goal_law(t[2],t[3],line,filename)
		#TODO: Ignore if empty.
		
##########################

	def p_if_part(self,t): # If parts can be empty
		''' if_part : 
					| IF formula '''
		if len(t) == 3:
			if t[2].is_false(): t[0] = t[2]
			elif len(t[2]) == 0: t[0] = None #TODO: is this required?
			else: t[0] = t[2]
		else: t[0] = None

	def p_after_part(self,t): # After parts canNOT be empty (dynamic laws are static laws without)
		''' after_part : AFTER formula '''
		if len(t[2]) == 0: t[0] = None
		else: t[0] = t[2]

	def p_ifcons_part(self,t): # Ifcons parts can be empty
		''' ifcons_part : 
					| IFCONS formula '''
		if len(t) == 3: 
			if type(t[2]) == ps.atom_list and len(t[2]) == 0: t[0] = None
			else: t[0] = t[2]
		else: t[0] = None

	def p_where_part(self,t):
		''' where_part : 
					| WHERE bindings '''
		if len(t) == 3: t[0] = t[2]
		else: t[0] = None
		
	def p_bindings(self,t):
		''' bindings : binding
					| bindings COMMA binding'''
		if len(t) == 2: 
			t[0] = ps.atom_list(t[1])
		else: 
			t[1].combine(t[3])
			t[0] = t[1]
		
	def p_binding(self,t):
		''' binding : ACT term
					| FLU term_equalpart
					| term_boolean'''
		if len(t) == 2: 
			t[0] = t[1] #ps.predicate(t[1],None)
		elif t[1] in ['<action>','action']:
			t[0] = ps.action(t[2])
		elif t[1] in ['<fluent>','fluent']:
			if type(t[2]) == ps.fluent_multival:
				t[0] = ps.fluent(t[2].content,t[2].multidomain)
			elif type(t[2]) == ps.equation:
				t[0] = ps.fluent(t[2].left,t[2].right)
			else:
				t[0] = ps.fluent(t[2])
			
	def p_term_equalpart(self,t):
		''' term_equalpart : term
					| term EQ term_numeric
					| term EQ LBRAC term_number_list RBRAC
					| term EQ term_numeric DDOT term_numeric'''
					#| term COLON term_numeric DDOT term_numeric'''
					#| term COLON LBRAC term_numeric DDOT term_numeric RBRAC '''
		if len(t) == 2: 
			t[0] = t[1]
		elif len(t) == 4: 
			t[0] = ps.equation(t[1],t[3])
		elif len(t) == 6:
			if t[4] == "..":
				t[0] = ps.fluent_multival(t[1],ps.value_range(t[3],t[5]))
				#if t[2]==":":
				#	t[0] = ps.fluent_multival(t[1],[t[3],t[5]],int_operator=True)
				#else:
				#	t[0] = ps.fluent_multival(t[1],ps.value_range(t[3],t[5]))
			else:
				t[0] = ps.fluent_multival(t[1],t[4])
		#elif len(t) == 8:
		#	t[0] = ps.fluent_multival(t[1],multidomain=ps.value_range(t[4],t[6]),int_operator=True)
			
##########################

	def p_binding_or_range(self,t):
		'''binding_or_range : term
							| term_numeric DDOT term_numeric'''
		if len(t) == 2:
			t[0] = t[1]
		else:
			t[0] = [t[1],t[3]]

	def p_formula(self,t):
		''' formula : term_boolean 
					| term_boolean COMMA formula
					| term_boolean COLON binding_or_range 
					| term_boolean COLON binding_or_range COMMA formula '''
		if len(t) == 4:
			if t[2] == ":":
				if t[1] is None: t[0] = ps.atom_list()
				elif t[1].is_false(): t[0] = t[1]
				else:
					t[1].binding = t[3] 
					t[0] = ps.atom_list(t[1])
			else:
				if t[1] is None: t[0] = t[3]
				elif t[1].is_false(): t[0] = t[1]
				elif t[3].is_false(): t[0] = t[3]
				else:
					t[3].combine(t[1])
					t[0] = t[3]
		elif len(t) == 6:
			if t[1] is None: t[0] = t[5]
			elif t[1].is_false():
				t[0] = t[1]
			elif t[5].is_false(): 
				#t[1].binding = t[5] 
				t[0] = t[5]
			else:
				t[1].binding = t[3]
				t[5].combine(t[1])
				t[0] = t[5]
		else:
			if t[1] is None: t[0] = ps.atom_list()
			elif t[1].is_false(): t[0] = t[1]
			else: t[0] = ps.atom_list(t[1])


	def p_fluent_formula(self,t): # f_1,...,f_n
		''' fluent_formula : term_equalpart
					| term_equalpart COMMA fluent_formula
					| term_equalpart COLON binding_or_range
					| term_equalpart COLON binding_or_range COMMA fluent_formula'''
		if len(t) == 4:
			if t[2] == ':':
				t[0] = ps.atom_list(ps.fluent_multival(t[1],t[3],int_operator=type(t[3]==list)))
			else:
				t[3].append(t[1])
				t[0] = t[3]
		elif len(t) == 6:
			res = ps.fluent_multival(t[1],t[3],int_operator=type(t[3]==list))
			t[5].append(res)
			t[0] = t[5]
		else:
			t[0] = ps.atom_list(t[1])
		
			
	def p_term_number_list(self,t):
		''' term_number_list : term_numeric
					| term_numeric COMMA term_number_list '''
		if len(t) == 2: 
			t[0] = ps.atom_list(t[1])
		else: 
			t[3].combine(t[1],reverse=True)
			t[0] = t[3]

	def p_term_boolean(self,t):
		''' term_boolean : term 
					| NOT term
					| MINUS term
					| asp_term '''
		if len(t) == 3:
			t[0] = ps.negation(t[2])
		else:
			if t[1] in ["true","<true>"]: t[0] = None #ps.atom_list()
			elif t[1] in ["false","<false>"]: t[0] = ps.false_atom()
			else: t[0] = t[1]

	def p_term_numeric(self,t):
		''' term_numeric : term
				| MINUS term
				| number '''
		if len(t) == 3:
			t[0] = ps.negation(t[2])
		else:
			t[0] = t[1]
			
	def p_term(self,t): # X, a, 3, X;Y, 1..Z
		''' term : variable 
				| identifier 
				| IDENTIFIER LBRAC term_number_list RBRAC
				| IDENTIFIER LBRAC term_number_list RBRAC APOS '''
		if len(t) == 2: 
			t[0] = t[1]
		elif len(t) == 6:
			t[0] = ps.predicate(t[1],t[3],apostroph=True) 
		else:
			t[0] = ps.predicate(t[1],t[3]) 
		
	def p_variable(self,t):
		''' variable : VARIABLE '''
		t[0] = ps.variable(t[1])
	
	def p_number(self,t):
		''' number : NUMBER
					| MINUS NUMBER '''
		if len(t) == 2: t[0] = t[1]
		else: t[0] = t[1]+t[2]
		
		
	def p_identifier(self,t):
		''' identifier : IDENTIFIER 
					| IDENTIFIER APOS
					| TRUE
					| FALSE '''
		if len(t) == 2:
			if t[1] in ["true","<true>"]: t[0] = t[1] #ps.unknown("true")
			elif t[1] in ["false","<false>"]: t[0] = t[1] #ps.false_atom() #unknown("false")
			else: t[0] = ps.unknown(t[1])
		else:
			t[0] = ps.unknown(t[1],apostroph=True)
		
#################
#expr --> expr + term | term
#term --> term * factor | factor
#factor --> ( expr ) | number
#number --> number digit | digit
#digit --> 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9	
#################

	def p_asp_term(self,t):
		''' asp_term : asp_operation asp_eqoperator asp_operation '''
		if t[2] == ":=":
			t[0] = ps.assignment(t[1],t[3])
		elif t[2] == "+=":
			t[0] = ps.incremental_assignment(t[1],t[3])
		elif t[2] == "-=":
			t[0] = ps.incremental_assignment(t[1],t[3],negated=True)
		else:
			t[0] = ps.equation(t[1],t[3],operator=t[2])
			
	def p_asp_eqoperator(self,t):
		''' asp_eqoperator : EQQ
							| EQ
							| NEQ 
							| LT 
							| GT 
							| LE 
							| GE 
							| ASSIGN
							| PLUSEQ
							| MINUSEQ '''
		t[0] = t[1]

	def p_asp_operation(self,t):
		''' asp_operation : asp_mult_operation
						| asp_operation PLUS asp_mult_operation
						| asp_operation MINUS asp_mult_operation
						| term_numeric DDOT term_numeric '''
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
		#''' asp_brac_operation : term_or_negated_ident
		#				| LBRAC asp_operation RBRAC '''
		''' asp_brac_operation : term_numeric
						| LBRAC asp_operation RBRAC '''
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
			self.parser = yacc.yacc(module=self, debug=True, outputdir=mypath, **kwargs) # SILENT MODE!
		else:
			self.parser = yacc.yacc(module=self, debug=False, optimize=False, outputdir=mypath, **kwargs) # SILENT MODE!
			#write_tables=False,
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
		
		if len(self.data['preds']) > 0: print "ASP Stuff: ","; ".join(str(x) for x in self.data['preds'])
		if len(self.data['actions']) > 0: print "Actions: ","; ".join(str(x) for x in self.data['actions'])
		if len(self.data['fluents']) > 0: print "Fluents: ","; ".join(str(x) for x in self.data['fluents'])
		if len(self.data['integers']) > 0: print "Integers: ","; ".join(str(x) for x in self.data['integers'])
		if len(self.data['defined_fluents']) > 0: print "defined_fluents: ","; ".join(str(x) for x in self.data['defined_fluents'])
		if len(self.data['static_laws']) > 0: print "static_laws: ","; ".join(str(x) for x in self.data['static_laws'])
		if len(self.data['dynamic_laws']) > 0: print "dynamic_laws: ","; ".join(str(x) for x in self.data['dynamic_laws'])
		if len(self.data['impossible_laws']) > 0: print "impossible_laws: ","; ".join(str(x) for x in self.data['impossible_laws'])
		if len(self.data['default_laws']) > 0: print "default_laws: ","; ".join(str(x) for x in self.data['default_laws'])
		if len(self.data['nonexecutable_laws']) > 0: print "nonexecutable_laws: ","; ".join(str(x) for x in self.data['nonexecutable_laws'])
		if len(self.data['inertial_laws']) > 0: print "inertial_laws: ","; ".join(str(x) for x in self.data['inertial_laws'])
		if len(self.data['initially_laws']) > 0: print "initially_laws: ","; ".join(str(x) for x in self.data['initially_laws'])
		if len(self.data['goals']) > 0: print "goals: ","; ".join(str(x) for x in self.data['goals'])
		if len(self.data['roles']) > 0: print "roles: ","; ".join(str(x) for x in self.data['roles'])
		
		if True:
			
			print "-------------------"
			
			if len(self.data['preds']) > 0: print "ASP Stuff: ","; ".join(x.typestr() for x in self.data['preds'])
			if len(self.data['actions']) > 0: print "Actions: ","; ".join(x.typestr() for x in self.data['actions'])
			if len(self.data['fluents']) > 0: print "Fluents: ","; ".join(x.typestr() for x in self.data['fluents'])
			if len(self.data['integers']) > 0: print "Integers: ","; ".join(x.typestr() for x in self.data['integers'])
			if len(self.data['defined_fluents']) > 0: print "defined_fluents: ","; ".join(x.typestr() for x in self.data['defined_fluents'])
			if len(self.data['static_laws']) > 0: print "static_laws: ","; ".join(x.typestr() for x in self.data['static_laws'])
			if len(self.data['dynamic_laws']) > 0: print "dynamic_laws: ","; ".join(x.typestr() for x in self.data['dynamic_laws'])
			if len(self.data['impossible_laws']) > 0: print "impossible_laws: ","; ".join(x.typestr() for x in self.data['impossible_laws'])
			if len(self.data['default_laws']) > 0: print "default_laws: ","; ".join(x.typestr() for x in self.data['default_laws'])
			if len(self.data['nonexecutable_laws']) > 0: print "nonexecutable_laws: ","; ".join(x.typestr() for x in self.data['nonexecutable_laws'])
			if len(self.data['inertial_laws']) > 0: print "inertial_laws: ","; ".join(x.typestr() for x in self.data['inertial_laws'])
			if len(self.data['initially_laws']) > 0: print "initially_laws: ","; ".join(x.typestr() for x in self.data['initially_laws'])
			if len(self.data['goals']) > 0: print "goals: ","; ".join(x.typestr() for x in self.data['goals'])
			#if len(self.data['roles']) > 0: print "roles: ","; ".join(x.typestr() for x in self.data['roles'])
			if len(self.data['roles']) > 0: print "roles: ","; ".join(str(x) for x in self.data['roles'])
		
		print "-------------------"
