import py

from js.astbuilder import Scopes

def test_scopes_is_local():
    scopes = Scopes()
    scopes.new_scope()
    assert scopes.get_local('a') is None
    scopes.add_local('a')
    assert scopes.get_local('a') is not None
    scopes.add_local('b')
    assert scopes.get_local('b') is not None
    scopes.new_scope()
    assert scopes.get_local('a') is None
    scopes.add_local('a')
    assert scopes.get_local('a') is not None
    assert scopes.get_local('b') is None

def test_scopes_get_local():
    scopes = Scopes()
    scopes.new_scope()
    scopes.add_local('a')
    scopes.add_local('b')
    assert scopes.get_local('a') == 0
    assert scopes.get_local('b') == 1
    assert scopes.get_local('c') is None

    scopes.new_scope()
    scopes.add_local('b')
    assert scopes.get_local('b') == 0
    assert scopes.get_local('a') is None

