import py

#from js.astbuilder import Scopes

#def test_scopes_is_local():
    #scopes = Scopes()

    #scopes.new_scope()
    #assert scopes.is_local('a') is False
    #scopes.add_local('a')
    #assert scopes.is_local('a') is True
    #assert scopes.is_local('b') is False
    #scopes.add_local('b')
    #assert scopes.is_local('b') is True

    #scopes.new_scope()
    #assert scopes.is_local('a') is False
    #scopes.add_local('a')
    #assert scopes.is_local('a') is True
    #assert scopes.is_local('b') is False

#def test_scopes_get_local():
    #scopes = Scopes()
    #scopes.new_scope()
    #scopes.add_local('a')
    #scopes.add_local('b')
    #assert scopes.get_local('a') == 0
    #assert scopes.get_local('b') == 1
    #py.test.raises(ValueError, scopes.get_local, 'c')

    #scopes.new_scope()
    #scopes.add_local('b')
    #assert scopes.get_local('b') == 0
    #py.test.raises(ValueError, scopes.get_local, 'a')

#def test_scopes_declare_local():
    #scopes = Scopes()
    #scopes.new_scope()
    #assert scopes.declarations() == []
    #assert scopes.is_local('a') is False
    #assert scopes.is_local('b') is False
    #assert scopes.is_local('c') is False
    #scopes.declare_local('a')
    #assert scopes.is_local('a') is True
    #assert scopes.is_local('b') is False
    #scopes.add_local('b')
    #assert scopes.is_local('b') is True
    #assert scopes.get_local('a') == 0
    #assert scopes.get_local('b') == 1
    #py.test.raises(ValueError, scopes.get_local, 'c')
    #assert scopes.declarations() == ['a']

