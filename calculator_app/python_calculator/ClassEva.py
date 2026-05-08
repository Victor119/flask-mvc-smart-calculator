"calculator_app/python_calculator/ClassEva.py"

import re
import math

def isNumber(exp):
    if isinstance(exp, int) or isinstance(exp, float):
        return True
    else:
        return False

def isString(exp):
    if isinstance(exp, str):
        return True
    else:
        return False

def isArray(exp):
    if type(exp) is list:
        return True
    else:
        return False

class Eva:
    infinit = 10000000000
    epsilon = 0.000000001
    pi = 3.1415926

    def diferitDeInfinit(self, x):
        return (self.infinit - abs(x)) > self.infinit / 2

    def modul(self, x):
        if self.diferitDeInfinit(x):
            return abs(x)
        else:
            return self.infinit

    def estePar(self, x):
        return (self.modul(x) % 2) == 0

    def logaritm(self, x):
        if x > self.epsilon and self.diferitDeInfinit(x):
            return math.log(x)
        return self.infinit

    def exponential(self, x):
        if self.diferitDeInfinit(x):
            return math.exp(x)
        else:
            return self.infinit

    def plus(self, x, y):
        if self.diferitDeInfinit(x) and self.diferitDeInfinit(y):
            return x + y
        return self.infinit

    def minus(self, x, y):
        if self.diferitDeInfinit(x) and self.diferitDeInfinit(y):
            return x - y
        return self.infinit

    def inmultit(self, x, y):
        if self.modul(x) < self.epsilon or self.modul(y) < self.epsilon:
            return 0
        if self.diferitDeInfinit(x) and self.diferitDeInfinit(y):
            return x * y
        return self.infinit

    def impartit(self, x, y):
        if self.modul(y) > self.epsilon:
            return x/y
        else:
            return self.infinit

    def putere(self, x, y):
        if x == 0:
            return 0
        elif y == 0:
            return 1
        else:
            if not self.diferitDeInfinit(x) or not self.diferitDeInfinit(x):
                return self.infinit
            elif y == int(y):
                #facem trunc ca daca primim ca input 2.0 sa il facem in 2
                y_i = math.trunc(y)
                p = 1
                i = 1
                while i <= y_i / 2:
                    p = p * x
                    p = p * p
                    i = i + 1
                #daca y este impar atunci mai inmultim o data la final
                if not self.estePar(y_i):
                    p = p * x
                return p
            else:
                return self.exponential(self.inmultit(y, self.logaritm(x)))

    def sinus(self, x):
        if self.diferitDeInfinit(x):
            return math.sin(x)
        else:
            return self.infinit

    def cosinus(self, x):
        if self.diferitDeInfinit(x):
            return math.cos(x)
        else:
            return self.infinit

    def radical(self, x):
        if (not self.diferitDeInfinit(x) or (x < self.epsilon)):
            return self.infinit
        return math.sqrt(x)

    def eval(self, exp):
        if isNumber(exp):
            return exp

        if isArray(exp):
            if exp[0] == "+":
                x = self.eval(exp[1])
                y = self.eval(exp[2])
                return self.plus(x, y)

            if exp[0] == "-":
                x = self.eval(exp[1])
                y = self.eval(exp[2])
                return self.minus(x, y)

            if exp[0] == "*":
                x = self.eval(exp[1])
                y = self.eval(exp[2])
                return self.inmultit(x, y)

            if exp[0] == "/":
                x = self.eval(exp[1])
                y = self.eval(exp[2])
                return self.impartit(x, y)

            if exp[0] == "^^":
                x = self.eval(exp[1])
                y = self.eval(exp[2])
                return self.putere(x, y)

            if exp[0] == "rad":
                x = self.eval(exp[1])
                return self.radical(x)

            if exp[0] == "log":
                x = self.eval(exp[1])
                return self.logaritm(x)

            if exp[0] == "sin":
                x = self.eval(exp[1])
                return self.sinus(x)

            if exp[0] == "cos":
                x = self.eval(exp[1])
                return self.cosinus(x)

        raise TypeError("Unimplemented")
