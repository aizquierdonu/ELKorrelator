#!/usr/bin/python
# -*- coding: iso-8859-15
print '''
input {
  tcp {
    port => 25555
    tags => ["new_elko"]
  }
}
input {
  tcp {
    port => 35555
    tags => ["del_elko"]
  }
}
'''
