
% Include initially statements
:- initially(val(V,X)), integer(V), not &sum{val(V,0)} = X.
holds(F,0) :- initially(F).

