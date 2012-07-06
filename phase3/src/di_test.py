# -*- coding: utf-8 -*-

logging.info('[exec]locals(): %s' % locals())

# get local namespace
ns = locals()['ns']

# define a function that will update working namespace
def update_namespace(ns, _locals):

	logging.info('[exec]updating namespace... %s' % _locals)
	
	# delete working namespace (assuming it is called ns)
	del _locals['ns']
	for k in _locals:
		ns[k] = _locals[k]	

	logging.info('[exec]done! %s' % ns)

# def functions
def f():
	return 1

# insert functions into local namespace
update_namespace(ns, locals())

def main(ns):

	# get method from namespace
	f = ns.get('f')

	# do stuff...
	x = f()
	# wow, x now has the value 1

	# get the update namespace function
	update_namespace = ns.get('update_namespace')
	# insert local variables into working namespace namespace
	update_namespace(ns, locals())

	# we are done. the executer can now access variables in ns
	logging.info('[exec]done!')

# call main entry point with given namespace
main(ns)