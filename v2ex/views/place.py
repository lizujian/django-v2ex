#!/usr/bin/env python
# coding=utf-8

import os
import re
import time
import datetime
import hashlib
import string
import random


from django.core.cache import cache
from django.db import models
#from google.appengine.ext.webapp import util
from django import template
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.shortcuts import render,redirect
from django.conf import settings

from django.db import models
from django.views.generic import View, ListView,TemplateView

from v2ex.babel.models import Member
from v2ex.babel.models import Counter
from v2ex.babel.models import Section
from v2ex.babel.models import Node
from v2ex.babel.models import Topic
from v2ex.babel.models import Reply
from v2ex.babel.models import Note
from v2ex.babel.models import Place
from v2ex.babel.models import PlaceMessage

from v2ex.babel.models import SYSTEM_VERSION

from v2ex.babel.security import *
from v2ex.babel.ua import *
from v2ex.babel.da import *
from v2ex.babel.l10n import *
from v2ex.babel.ext.cookies import Cookies

#template.register_template_library('v2ex.templatetags.filters')

class PlaceHandler(View):
    def get(self, request, ip):
        site = GetSite()
        template_values = {}
        template_values['site'] = site
        template_values['rnd'] = random.randrange(1, 100)
        member = CheckAuth(self)
        if member:
            template_values['member'] = member
        l10n = GetMessages(self, member, site)
        template_values['l10n'] = l10n
        template_values['ip'] = ip
        substance = GetPlaceByIP(ip)
        if substance:
            template_values['substance'] = substance
            #template_values['messages'] = db.GqlQuery("SELECT * FROM PlaceMessage WHERE place = :1 ORDER BY created DESC LIMIT 30", substance)
            template_values['messages'] = PlaceMessage.objects.filter(place =substance).order_by('-created')[:30]
        else:
            if member:
                if member.ip == ip:
                    substance = CreatePlaceByIP(ip)
                    template_values['substance'] = substance
        can_post = False
        can_see = True
        if member:
            if member.ip == ip:
                can_post = True
                can_see = True
            else:
                can_see = False
        else:
            if 'X-Real-IP' in self.request.META:
                ip_guest = self.request.META['X-Real-IP']
            else:
                ip_guest = self.request.META['REMOTE_ADDR']
            if ip_guest == ip:
                can_see = True
            else:
                can_see = False
        template_values['can_post'] = can_post
        template_values['can_see'] = can_see
        if member:
            template_values['ip_guest'] = member.ip
        else:
            template_values['ip_guest'] = ip_guest
        template_values['page_title'] = site.title + u' › ' + ip
        path = 'desktop/place.html'
        #output = template.render(path, template_values)
        #self.response.out.write(output)
        return render(request, path, template_values)
    
    def post(self, request, ip):
        site = GetSite()
        if 'HTTP_REFERER' in self.request.META:
            go = self.request.META['HTTP_REFERER']
        else:
            go = '/place'
        member = CheckAuth(self)
        place = GetPlaceByIP(ip)
        say = self.request.POST.get('say').strip()
        if len(say) > 0 and len(say) < 280 and member and place:
            if member.ip == ip:
                message = PlaceMessage()
                #q = db.GqlQuery('SELECT * FROM Counter WHERE name = :1', 'place_message.max')
                q = Counter.objects.filter(name = 'place_message.max')
                if (q.count() == 1):
                    counter = q[0]
                    counter.value = counter.value + 1
                else:
                    counter = Counter()
                    counter.name = 'place_message.max'
                    counter.value = 1
                #q2 = db.GqlQuery('SELECT * FROM Counter WHERE name = :1', 'place_message.total')
                q2 = Counter.objects.filter(name = 'place_message.total')
                if (q2.count() == 1):
                    counter2 = q2[0]
                    counter2.value = counter2.value + 1
                else:
                    counter2 = Counter()
                    counter2.name = 'place_message.total'
                    counter2.value = 1
                message.num = counter.value
                message.place = place
                message.place_num = place.num
                message.member = member
                message.content = say
                message.in_reply_to = None
                message.save()
                counter.save()
                counter2.save()
        #self.redirect(go)
        return redirect(go)

class PlaceMessageRemoveHandler(View):
    def get(self, request, key):
        if 'HTTP_REFERER' in self.request.META:
            go = self.request.META['HTTP_REFERER']
        else:
            go = '/place'
        member = CheckAuth(self)
        if member:
            message = db.get(db.Key(key))
            if message:
                if message.member.num == member.num:
                    message.delete()
                    #q = db.GqlQuery('SELECT * FROM Counter WHERE name = :1', 'place_message.total')
                    q = Counter.objects.filter(name = 'place_message.total')
                    if (q.count() == 1):
                        counter = q[0]
                        counter.value = counter.value - 1
                        counter.save()
        #self.redirect(go)
        return redirect(go)

def main():
    application = webapp.WSGIApplication([
    ('/place/([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', PlaceHandler),
    ('/remove/place_message/(.*)', PlaceMessageRemoveHandler)
    ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()