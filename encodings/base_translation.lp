%%% Transitions
#include "base.lp".

%%% Rule translation

% Inertials
dynamic_law(id(inertial,F,V)) :- inertial(F), domain(F,V).
head(id(inertial,F,V),val(F,V)) :- inertial(F), domain(F,V).
after(id(inertial,F,V),val(F,V)) :- inertial(F), domain(F,V).
ifcons(id(inertial,F,V),val(F,V)) :- inertial(F), domain(F,V).

% Defaults
static_law(id(default,F)) :- default(F).
head(id(default,F),F) :- default(F).
ifcons(id(default,F),F) :- default(F).

static_law(L) :- default(L,_), not after(L,_).
dynamic_law(L) :- default(L,_), after(L,_).
head(L,F) :- default(L,F).
ifcons(L,F) :- default(L,F).

% Impossible laws
static_law(id(impossible,I)) :- impossible(I,_). 
head(id(impossible,I),_false) :- impossible(I,_). 
if(id(impossible,I),F) :- impossible(I,F). 


% Nonexecutable laws
dynamic_law(id(nonexecutable,I)) :- nonexecutable(I,_).
head(id(nonexecutable,I),_false) :- nonexecutable(I,_).
after(id(nonexecutable,I),F) :- nonexecutable(I,F).

