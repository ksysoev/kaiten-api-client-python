#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Exception classes are located  here
'''

class InvalidResponseFormat(Exception):
    """Error when the response which was gotten from api server couldn't be deserialize"""
    def __init__(self, path, method, body):
        self.path = path
        self.method = method
        self.body = body

        Exception.__init__(self)

    def __str__(self):
        return "Can't parse response from {} with method {}".format(
            self.path, self.method
        )

class UnauthorizedAccess(Exception):
    """Error when username or/and password are incorrect"""
    def __init__(self, username):
        self.username = username
        Exception.__init__(self)

    def __str__(self):
        return "Fail to get access for {}".format(self.username)

class AccessDenied(Exception):
    """Error when access for username for requested resource is denied"""
    def __init__(self, username, path, method):
        self.username = username
        self.path = path
        self.method = method

        Exception.__init__(self)

    def __str__(self):
        return "For {} access denied to {} with method {}".format(
            self.username, self.path, self.method
        )

class UnexpectedError(Exception):
    """Error when response has unexpected response code"""
    def __init__(self, status, path, method, body):
        self.status = status
        self.path = path
        self.method = method
        self.body = body

        Exception.__init__(self)

    def __str__(self):
        return "For {} with method {} is got unexpected status code {}".format(
            self.path, self.method, self.status
        )
