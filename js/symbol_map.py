from js.object_map import new_map


class SymbolMap(object):
    def __init__(self):
        self.symbols = new_map()
        self.functions = []
        self.variables = []
        self.parameters = []

    def add_symbol(self, identifyer):
        idx = self.symbols.lookup(identifyer)

        if idx == self.symbols.NOT_FOUND:
            self.symbols = self.symbols.add(identifyer)
            idx = self.symbols.lookup(identifyer)

        assert isinstance(idx, int)
        return idx

    def add_variable(self, identifyer):
        idx = self.add_symbol(identifyer)

        self.variables.append(identifyer)
        return idx

    def add_function(self, identifyer):
        idx = self.add_symbol(identifyer)

        self.functions.append(identifyer)
        return idx

    def add_parameter(self, identifyer):
        #assert isinstance(identifyer, unicode)
        f = unicode(identifyer)
        #assert isinstance(f, unicode)
        idx = self.add_symbol(f)
        self.parameters.append(f)
        return idx

    def get_index(self, identifyer):
        return self.symbols.lookup(identifyer)

    def get_symbols(self):
        return self.symbols.keys()

    def len(self):
        return self.symbols.len()

    def finalize(self):
        return FinalSymbolMap(self.symbols, self.functions, self.variables, self.parameters)


class FinalSymbolMap(object):
    _immutable_fields_ = ['symbols', 'functions[*]', 'variables[*]', 'parameters[*]']

    def __init__(self, symbols, functions, variables, parameters):
        self.symbols = symbols
        self.functions = functions[:]
        self.variables = variables[:]
        self.parameters = parameters[:]

    def get_index(self, identifyer):
        return self.symbols.lookup(identifyer)

    def get_symbols(self):
        return self.symbols.keys()

    def len(self):
        return self.symbols.len()
