#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client functionality for Kaiten API.
"""

import http.client
import base64
import json
import weakref
import pprint
import urllib

from kaiten.exceptions import *



API_VERSION = 'v1'
USER_AGENT  = "KaitenAPIClientPython"


class KaitenObject (object):
    __parent = None

    def __str__(self):
        return  pprint.PrettyPrinter( indent = 4 ).pformat( self.__dict__ )

    def __init__( self, parent, data={} ):
        self.__parent = weakref.ref( parent )
        for key in data: setattr( self, key, data[key] )

    def __get_parent__(self):
        return self.__parent()

    def __get_item_by_id__(self, path, item_class, id, params = {}):
        item = self.__request__( 'GET', path + '/' + str(id), params)
        return globals()[ item_class ](self, item)

    def __get_items__(self, path, item_class, params = {}):
        items = self.__request__('GET', path, params)
        return [ globals()[ item_class ]( self, item ) for item in items ]

    def __update__(self, item_class, params ):
        data = self.__request__('PATCH', '', params)
        for key in data: setattr( self, key, data[key] )

    def __delete__(self, params = {}):
        self.__request__('DELETE', '', params)

    def __create_item__(self, path, item_class, params ):
        item = self.__request__('POST', path, params)
        return globals()[ item_class ](self, item)

    def __request__(self, method, path, params = {}):
        path = path if path and path[0] == '/' else  ( self.__get_uri__() + '/' + path )
        return self.__get_parent__().__request__( method, path, params )

    def __get_uri__(self):
        raise NotImplementedError('You should implement methot __get_uri__ in descendant class')

    def __deserialize_item__( self, field, item_class, data ):
        if field in data :
            setattr( self, field,  globals()[ item_class ]( self, data.pop(field) ) )

    def __deserialize_list__( self, field, item_class, data ):
        setattr( self, field, [] )
        if field in data :
            for item in data.pop(field):
                getattr(self, field).append( globals()[ item_class ](self, item) )


class Client (KaitenObject):
    """Performs requests to the Kaiten API service."""

    END_POINT = '/api/' + API_VERSION

    host = None
    username = None
    password = None
    debug = False

    def __init__(self, host, username, password, debug=False ):
        """
        :param host: IP or hostname of Kaiten server
        :type host: string
        :param username: Login name for connection
        :type username: string
        :param password: User's password for connection
        :type password: string
        :param debug: this is a flag, which enables printing debug informationю
        :type channel: bool
        """
        self.host = host
        self.username = username
        self.password = password
        self.debug = debug


    def __request__(self, method, path, params = {}):
        """Performs HTTP request with credentials, returning the deserialized body json of request
        :param method: Method name for HTTP request
        :type method: string
        :param path: Absolut path after entry point of API( /api/v1 )
        :type path: string
        :param params: Parameters for HTTP Request,
            which will be serialized to json and putted in request body
        :type params: dict
        """
        conn = http.client.HTTPSConnection( self.host )

        request_body = ''
        if method == 'GET' :
            query_string = urllib.parse.urlencode(params)
            if query_string:
                path = '?'.join([ path, query_string ])
        else :
            request_body = json.dumps(params)

        conn.request(
            method,
            self.__get_url_for__(path),
            request_body,
            self.__get_headers__(),
        )

        if self.debug :
            print(
                "Sending request to {} with method {}.\nRequest body:\n{}\n".format(
                    path, method, request_body
                )
            )
        resp = conn.getresponse()

        body = resp.read().decode()
        if self.debug :
            print(
                "Response code: {}\nResponse body:\n{} \n".format(
                    resp.status, body
                )
            )

        if resp.status == 200:
            try:
                return json.loads(body)
            except json.decoder.JSONDecodeError:
                raise InvalidResponseFormat( path, method, body )
        elif resp.status == 401:
            raise UnauthorizedAccess( self.username )
        elif resp.status == 403:
            raise AccessDenied( self.username, path, method )
        else:
            raise UnexpectedError( resp.status, path, method, body )

    def __get_url_for__(self, path):
        """Returns absolute path for request with entry point of API
        :param path: Absolut path after entry point of API( /api/v1 )
        :type path: string
        """
        return self.END_POINT + ( path if path[0] == '/' else  '/' + path )

    def __get_headers__(self):
        """Returns HTTP headers for request"""
        return {
            'Authorization': self.__get_auth_key__(),
            'Content-Type' : 'application/json',
            'User-Agent'   : USER_AGENT,
        }

    def __get_auth_key__(self):
        """Returns auth key for API"""
        user_pass = ":".join( [ self.username, self.password ] )
        key = base64.b64encode( user_pass.encode('utf8') )
        return "Basic " + key.decode('utf8');

    def get_spaces(self):
        """Returns a list of all avalible spaces"""
        return self.__get_items__('/spaces', 'Space')

    def get_space(self, id):
        """Returns a space with requested id
        :param id: id of requested space
        :type id: int
        """
        return self.__get_item_by_id__('/spaces', 'Space', id)

    def create_space(self, title):
        """Creates a new space and after that returns the space
        :param title: name of a new space
        :type method: string
        """
        return self.__create_item__('/spaces', 'Space', { 'title': title })

    def get_cards(self, params = {}):
        """Returns a list of all cards which fits to requested parameters.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-get
        :type params: dict
        """
        return self.__get_items__('/cards', 'Card', params)

    def get_card(self, id):
        """Returns a card with requested id
        :param id: id of requested card
        :type id: int
        """
        return self.__get_item_by_id__('/cards', 'Card', id)

    def get_users(self):
        """Returns a list of all avalible users"""
        return self.__get_items__('/users', 'User')

    def get_user(self, id):
        """Returns a user with requested id
        :param id: id of requested user
        :type id: int
        """
        return self.__get_item_by_id__('/users', 'User', id)

    def get_tags(self):
        """Returns a list of all avalible tags"""
        return self.__get_items__('/tags', 'Tag')

    def get_card_types(self):
        """Returns a list of all avalible card types"""
        return self.__get_items__('/card-types', 'CardType')

    def create_card_type(self, letter, name, color):
        """Adds new card type
        :param letter: Character that represents type
        :type letter: string
        :param name: Type name
        :type name: string
        :param color: Color number
        :type color: int
        """
        return self.__create_item__(
            '/card-types',
            'CardType',
            { 'letter': letter, 'name': name, 'color': color }
        )

class Space (KaitenObject):
    def __init__(self, parent, data={}):
        self.__deserialize_list__('boards', 'Board', data)

        KaitenObject.__init__( self, parent, data )

    def __get_uri__(self):
        return '/spaces/' + str(self.id)

    def update(self, params={}):
        """Updates the space.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#spaces-patch
        :type params: dict
        """
        return self.__update__( 'Space', params )

    def get_boards(self):
        """Returns a list of all avalible boards for the current space"""
        return self.__get_items__('boards', 'Board')

    def get_board(self, id):
        """Returns a board with requested id
        :param id: id of requested board
        :type id: int
        """
        return self.__get_item_by_id__('boards', 'Board', id)

    def create_board(self, title, params={}):
        """Creates a new board
        :param title: Title of the new board
        :type title: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#boards-post
        :type params: dict
        """
        params['title'] = title
        return self.__create_item__('boards', 'Board', params)

    def get_cards(self, params = {}):
        """Returns a list of all cards for that space which fits to requested parameters.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-get
        :type params: dict
        """
        params['space_id'] = self.id
        return self.__get_parent__().get_cards(params)

    def get_users(self):
        """Returns a list of all avalible users for the current space"""
        return self.__get_items__('users', 'User')

    def get_user(self, id):
        """Returns a user with requested id
        :param id: id of requested user
        :type id: int
        """
        return self.__get_item_by_id__('users', 'User', id)

    def create_card(self, board_id, column_id, lane_id, title, params={}):
        """Adds new card type in current space
        :param title: Title of new card
        :type title: string
        :param board_id: Board ID
        :type board_id: int
        :param column_id: Column ID
        :type column_id: int
        :param lane_id: Lane ID
        :type lane_id: int
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-post
        :type params: dict
        """
        params['space_id']  = self.id
        params['board_id']  = board_id
        params['column_id'] = column_id
        params['lane_id']   = lane_id
        params['title']     = title

        return self.__create_item__('/cards', 'Card', params)


class Board (KaitenObject):
    def __init__(self, parent, data={}):
        self.__deserialize_list__('columns', 'Column', data)
        self.__deserialize_list__('lanes', 'Lane', data)
        self.__deserialize_list__('cards', 'Card', data)

        KaitenObject.__init__( self, parent, data )

    def __get_uri__(self):
        return '/boards/' + str(self.id)

    def update(self, params={}):
        """Updates the board.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#boards-patch
        :type params: dict
        """
        return self.__update__( 'Board', params )

    def delete(self):
        """Deletes this board
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#boards-delete
        :type params: dict
        """
        return self.__delete__()

    def create_column(self, title, params={}):
        """Creates a new column
        :param title: Title of the new column
        :type title: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#columns-post
        :type params: dict
        """
        params['title'] = title
        return self.__create_item__('columns', 'Column', params)

    def create_lane(self, title, params={}):
        """Creates a new lane
        :param title: Title of the new lane
        :type title: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#lanes-post
        :type params: dict
        """
        params['title'] = title
        return self.__create_item__('lanes', 'Lane', params)

    def get_cards(self, params = {}):
        """Returns a list of all cards for that board which fits to requested parameters.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-get
        :type params: dict
        """
        params['board_id'] = self.id
        return self.__get_parent__().get_cards(params)

    def create_card(self, column_id, lane_id, title, params={}):
        """Adds new card type in current board
        :param title: Title of new card
        :type title: string
        :param column_id: Column ID
        :type column_id: int
        :param lane_id: Lane ID
        :type lane_id: int
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-post
        :type params: dict
        """
        return self.__get_parent__().create_card(
            board_id  = self.id,
            column_id = column_id,
            lane_id   = lane_id,
            title     = title,
            params    = params,
        )

class Column (KaitenObject):
    def __get_uri__(self):
        return 'columns/' + str(self.id)

    def update(self, params={}):
        """Updates the column.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#columns-patch
        :type params: dict
        """
        return self.__update__( 'Column', params )

    def delete(self, params={}):
        """Deletes this column
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#columns-delete
        :type params: dict
        """
        return self.__delete__(params)

    def get_cards(self, params = {}):
        """Returns a list of all cards for that column which fits to requested parameters.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-get
        :type params: dict
        """
        params['column_id'] = self.id
        return self.__get_parent__().get_cards(params)

    def create_card(self, lane_id, title, params={}):
        """Adds new card type in current column
        :param title: Title of new card
        :type title: string
        :param lane_id: Lane ID
        :type lane_id: int
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-post
        :type params: dict
        """
        return self.__get_parent__().create_card(
            column_id = self.id,
            lane_id   = lane_id,
            title     = title,
            params    = params,
        )


class Lane (KaitenObject):
    def __get_uri__(self):
        return 'lanes/' + str(self.id)

    def update(self, params={}):
        """Updates the lane.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#lanes-patch
        :type params: dict
        """
        return self.__update__( 'Lane', params )

    def delete(self, params={}):
        """Deletes this lane
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#lanes-delete
        :type params: dict
        """
        return self.__delete__(params)

    def get_cards(self, params = {}):
        """Returns a list of all cards for that lane which fits to requested parameters.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-get
        :type params: dict
        """
        params['lane_id'] = self.id
        return self.__get_parent__().get_cards(params)

    def create_card(self, column_id, title, params={}):
        """Adds new card type in current lane
        :param title: Title of new card
        :type title: string
        :param column_id: Column ID
        :type column_id: int
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#cards-post
        :type params: dict
        """
        return self.__get_parent__().create_card(
            lane_id   = self.id,
            column_id = column_id,
            title     = title,
            params    = params,
        )

class User (KaitenObject):
    pass

class TimeSheet (KaitenObject):
    pass

class Card (KaitenObject):
    def __init__(self, parent, data={}):
        self.__deserialize_item__('type', 'CardType', data)
        self.__deserialize_list__('tags', 'Tag', data)
        self.__deserialize_list__('members', 'User', data)
        self.__deserialize_item__('owner', 'User', data)
        self.__deserialize_list__('parents', 'Card', data)
        self.__deserialize_list__('children', 'Card', data)
        self.__deserialize_list__('checklists', 'Checklist', data)
        self.__deserialize_list__('files', 'CardFile', data)

        if 'board' in data :
            self.board = Board( self, data.pop('board') )
            if 'column' in data :
                self.board = Column( self.board, data.pop('column') )
            if 'lane' in data :
                self.board = Lane( self.board, data.pop('lane') )
        else :
            if 'column' in data :
                del data['column']
            if 'lane' in data :
                del data['lane']

        KaitenObject.__init__( self, parent, data )

    def __get_uri__(self):
        return '/cards/' + str(self.id)

    def arhive(self):
        """Puts the card to arhive"""
        return self.__update__( 'Card', { 'condition' : 2 } )

    def unarhive(self):
        """Returns the card from arhive"""
        return self.__update__( 'Card', { 'condition' : 1 } )

    def unblock(self):
        """Unblocks card"""
        return self.__update__( 'Card', { 'blocked' : False } )

    def block(self, params={}):
        """Creates card blocker
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#lanes-post
        :type params: dict
        """
        return self.__create_item__('blockers', 'CardBlocker', params)

    def add_tag(self, name):
        """Adds new tag to card
        :param text: Tag's name
        :type text: string
        """
        return self.__create_item__('tags', 'Tag', { 'name' : name })

    def add_comment(self, text, params={}):
        """Adds new comment to card
        :param text: Comment text
        :type text: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-comments-post
        :type params: dict
        """
        params['text'] = text
        return self.__create_item__('comments', 'Comment', params)

    def add_external_link(self, url, params={}):
        """Adds new external link to card
        :param url: URL
        :type url: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-external-links-post
        :type params: dict
        """
        params['url'] = url
        return self.__create_item__('external-links', 'ExternalLink', params)

    def add_child(self, card_id):
        """Adds new child card
        :param card_id: ID of child card
        :type card_id: int
        """
        params['card_id'] = text
        return self.__create_item__('external-links', 'ExternalLink', params)

    def get_time_logs(self):
        """Returns a list of time logs"""
        return self.__get_items__('time-logs', 'CardTimeLog')

    def add_time_log(self, role_id, time_spent, for_date,  params={}):
        """Adds new time log to card
        :param role_id: Role id, predefined role is: -1 - Employee
        :type role_id: int
        :param time_spent: amount of time in minutes
        :type time_spent: int
        :param for_date: Log date in format YYYY-MM-DD, for example 2025-12-24
        :type for_date: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-time-logs,-not-stable-yet-post
        :type params: dict
        """
        params['role_id']    = role_id
        params['time_spent'] = time_spent
        params['for_date']   = for_date
        return self.__create_item__('time-logs', 'CardTimeLog', params)

    def add_checklist(self, name, params={}):
        """Adds new check list to card
        :param name: name of check list
        :type name: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-checklists-post
        :type params: dict
        """
        params['name']    = name
        return self.__create_item__('checklists', 'Checklist', params)

    def add_definition_of_done(self, text, params={}):
        """Adds new definition of done to card
        :param text: Content of item
        :type text: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-definition-of-done-&#40;acceptance-criteria&#41;-post
        :type params: dict
        """
        params['text'] = text
        return self.__create_item__('definition-of-done', 'CardDefinitionOfDone', params)

class Tag (KaitenObject):
    def __get_uri__(self):
        return 'tags/' + str(self.id)

    def delete(self):
        """Deletes this tag"""
        return self.__delete__()

class ExternalLink (KaitenObject):
    def __get_uri__(self):
        return 'external-links/' + str(self.id)

    def update(self, params={}):
        """Updates the external link.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-external-links-patch
        :type params: dict
        """
        return self.__update__( 'ExternalLink', params )

    def delete(self):
        """Deletes this external link"""
        return self.__delete__()

class Comment (KaitenObject):
    def __get_uri__(self):
        return 'comments/' + str(self.id)

    def update(self, params={}):
        """Updates the comment.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-comments-patch
        :type params: dict
        """
        return self.__update__( 'Comment', params )

    def delete(self):
        """Deletes this comment"""
        return self.__delete__()

class CardType (KaitenObject):
    def __get_uri__(self):
        return '/card-types/' + str(self.id)

    def update(self, params={}):
        """Updates the card type.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-types-patch
        :type params: dict
        """
        return self.__update__( 'CardType', params )

    def delete(self):
        """Deletes this card type"""
        return self.__delete__()

class CardChild (KaitenObject):
    def __get_uri__(self):
        return 'children/' + str(self.id)

    def delete(self):
        """Deletes this card child"""
        return self.__delete__()

class CardBlocker (KaitenObject):
    pass

class CardFile (KaitenObject):
    def __init__(self, parent, data={}):
        self.__deserialize_item__('author', 'User', data)

class CardTimeLog (KaitenObject):
    def __get_uri__(self):
        return 'time-logs/' + str(self.id)

    def update(self, params={}):
        """Updates the card time log.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-time-logs,-not-stable-yet-patch
        :type params: dict
        """
        return self.__update__( 'CardTimeLog', params )

    def delete(self):
        """Deletes this time log"""
        return self.__delete__()

class CardDefinitionOfDone (KaitenObject):
    def __get_uri__(self):
        return 'definition-of-done/' + str(self.id)

    def update(self, params={}):
        """Updates the definition of done.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-definition-of-done-&#40;acceptance-criteria&#41;-patch
        :type params: dict
        """
        return self.__update__( 'CardDefinitionOfDone', params )

    def delete(self):
        """Deletes this definition of done"""
        return self.__delete__()

class Checklist (KaitenObject):
    def __init__(self, parent, data={}):
        self.__deserialize_list__('items', 'ChecklistItem', data)

        KaitenObject.__init__( self, parent, data )

    def __get_uri__(self):
        return 'checklists/' + str(self.id)

    def update(self, params={}):
        """Updates the check list.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-checklists-patch
        :type params: dict
        """
        return self.__update__( 'Checklist', params )

    def delete(self):
        """Deletes this checklist"""
        return self.__delete__()

    def add_item(self, text, params={}):
        """Adds new item to check list
        :param text: text for new item
        :type text: string
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-checklist-items-post
        :type params: dict
        """
        params['text'] = text
        return self.__create_item__('items', 'ChecklistItem', params)

class ChecklistItem (KaitenObject):
    def __get_uri__(self):
        return 'items/' + str(self.id)

    def update(self, params={}):
        """Updates the check list item.
        :param params: Dictionary with parametrs for request.
            Full list of avalible parameters is avalible on
            https://faq.kaiten.io/docs/api#card-checklist-items-patch
        :type params: dict
        """
        return self.__update__( 'ChecklistItem', params )

    def delete(self):
        """Deletes this check list item"""
        return self.__delete__()