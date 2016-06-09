''' Custom Template Tags '''
import collections

from django import template
from django.conf import settings

from elastic.elastic_settings import ElasticSettings
from elastic.result import Document


register = template.Library()


@register.filter
def doc_attr(doc, arg):
    ''' Gets attribute of an object dynamically from a string name '''
    return getattr(doc, arg, None) if isinstance(doc, Document) \
        else settings.TEMPLATE_STRING_IF_INVALID


@register.filter
def doc_attr_str(doc, arg):
    ''' Gets attribute of an object dynamically from a string name '''
    attr = doc_attr(doc, arg)
    if isinstance(attr, str):
        return attr
    elif isinstance(attr, list):
        return '; '.join([at for at in attr if at is not None])
    elif isinstance(attr, dict):
        return '; '.join([k + ':' + str(v) for k, v in attr.items()])
    else:
        return attr


@register.filter
def get_item(dictionary, key):
    ''' Get an item from the dictionary. '''
    return dictionary.get(key)


@register.filter
def doc_keys(doc):
    ''' Gets the keys of the document object. '''
    return sorted(list(doc.__dict__.keys())) if isinstance(doc, Document) \
        else settings.TEMPLATE_STRING_IF_INVALID


@register.filter
def doc_type(doc):
    ''' Gets the document type. '''
    return doc.type() if isinstance(doc, Document) \
        else settings.TEMPLATE_STRING_IF_INVALID


@register.filter
def doc_id(doc):
    ''' Gets the document ID. '''
    return doc.doc_id() if isinstance(doc, Document) \
        else settings.TEMPLATE_STRING_IF_INVALID


@register.filter
def doc_idx(doc):
    ''' Gets the document ID. '''
    return doc.index() if isinstance(doc, Document) \
        else settings.TEMPLATE_STRING_IF_INVALID


@register.filter
def doc_link(doc):
    ''' Gets the document details. '''
    return ElasticSettings.url() + '/' + doc.index() + '/' + doc.type() + \
        '/' + doc.doc_id() + '?routing=' + doc.doc_id() \
        if isinstance(doc, Document) else settings.TEMPLATE_STRING_IF_INVALID


@register.filter(name='sort')
def listsort(value):
    ''' Sort list and iterable arguments. '''
    if isinstance(value, list):
        try:
            new_list = list(value)
            new_list.sort()
            return new_list
        except TypeError:
            # sorting a list of dictionaries?
            if 'key' in value[0]:
                return sorted(value, key=lambda k: k['key'])
    elif isinstance(value, collections.Iterable):
        return sorted(value)
    return value

listsort.is_safe = True
