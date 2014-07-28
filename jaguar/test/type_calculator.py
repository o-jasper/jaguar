from jaguar import *

assert type_of(astify(['to_tuple', ['tuple', 'a_to_bbb'], 'x'])) == ['tuple', 'bbb']

print(calc_type(astify(['+', '1', '2325325'])))
