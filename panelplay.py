import param

class A(param.Parameterized):
    title = param.String(default='sum', doc='Title for the result')

class B(A):
    a = param.Integer(2, bounds=(0,10), doc='First addend')
    b = param.Integer(3, bounds=(0,10), doc='Second addend')

    def __call__(self):
        return self.title + ': ' + str(self.a + self.b)

