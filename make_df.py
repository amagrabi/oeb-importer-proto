#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Queries the commercetools API to creates DataFrames from json-formatted data 
of the following objects:
    
    - Products (from Product Projections, default staged='false')
    - Customers
    - Orders
    - Categories
    
Functions allow to select specific subsets of the data (via offset and nr_items).
To query the whole data, functions in make_df_full.py are more efficient.
    
@author: amagrabi


"""

import pandas as pd
import numpy as np

import config
from api import login, query
from api_util import get_product_price


def products(nr_items, staged='false', offset=0, size_chunks = 250,
             languages=['en','de'], currencies=['USD','EUR'],
             verbose=True):
    '''Queries the commercetools API to create a DataFrame of products.
    
    Args:
        nr_items: Maximum number of retrieved items.
        staged: Flag to get staged or non-staged items.
        offset: offset of retrieved items (i.e. offset=5 will omit the first 6 items).
        
    Returns:
        DataFrame of products.
        
    '''
    
    if nr_items <= 0:
        raise Exception('Parameter nr_items has to be larger than 0.')
    if staged not in ['true','false']:
        raise Exception('Parameter staged has to be either true or false.')
    
    auth = login(config.CLIENT_ID, config.CLIENT_SECRET, config.PROJECT_KEY, 
                 config.SCOPE, config.HOST)   
    
    # To do: dynamic assignment via dictionaries
#    fields_mandatory = {'id': "['id']",
#                        'createdAt': "['createdAt']"}
#
#    fields_optional = {'sku': "['masterVariant']['sku']",
#                       'img': "['masterVariant']['images'][0]['url']"}
    
    cols = ['id','sku','categoryIds','img','createdAt']
    
    # Language-dependent variables
    ld_vars = ['name', 'slug', 'description']
    [cols.append(ld_var + '_' + language) for ld_var in ld_vars for language in languages]
    # Currency-dependent variables
    cd_vars = ['price']
    [cols.append(cd_var + '_' + currency) for cd_var in cd_vars for currency in currencies]
    
    df = pd.DataFrame(index=[], columns=cols)
    
    limit = nr_items if nr_items <= size_chunks else size_chunks
    
    while True:
        
        if verbose:
            print('Loading products chunk (offset: {}, chunk size = {}, nr = {})'.format(offset, size_chunks, nr_items))
        
        endpoint = 'product-projections?limit={}&offset={}&staged={}'.format(limit, offset, staged)
        data_json = query(endpoint, config.PROJECT_KEY, auth, config.HOST)
        
        df_chunk = pd.DataFrame(index=[], columns=cols)
        results = data_json['results']

        for i, product in enumerate(results):
            
            # Mandatory fields
            df_chunk.loc[i, 'id'] = product['id']
            df_chunk.loc[i, 'createdAt'] = product['createdAt']

            # Optional fields
            try:
                df_chunk.loc[i, 'sku'] = product['masterVariant']['sku']
            except:
                df_chunk.loc[i, 'sku'] = ''
                
            try:
                df_chunk.loc[i, 'img'] = product['masterVariant']['images'][0]['url']
            except:
                df_chunk.loc[i, 'img'] = ''
            
            # Language-dependent variables
            for ld_var in ld_vars:
                for language in languages:
                    var = ld_var + '_' + language
                    try:
                        df_chunk.loc[i, var] = product[ld_var][language]
                    except:
                        df_chunk.loc[i, var] = ''
                    
            # Currency-dependent variables
            for cd_var in cd_vars:
                for currency in currencies:
                    var = cd_var + '_' + currency
                    df_chunk.loc[i, var] = get_product_price(product['masterVariant']['prices'], currency)

            # Categories
            cats_json = product['categories']
            cats_list = []
            for cat_json in cats_json:
                cats_list.append(cat_json['id'])
            df_chunk.loc[i, 'categoryIds'] = cats_list
                
                
        if nr_items <= size_chunks:
            df = df.append(df_chunk, ignore_index=True)
            return df
        else:
            nr_items -= size_chunks
            offset += size_chunks
            limit = nr_items if nr_items <= size_chunks else size_chunks
            df = df.append(df_chunk, ignore_index=True)
            

def customers(nr_items, offset=0, size_chunks = 250, verbose=True):
    '''Queries the commercetools API to create a DataFrame of customers.
    
    Args:
        nr_items: Maximum number of retrieved items.
        offset: offset of retrieved items (i.e. offset=5 will omit the first 6 items).
        
    Returns:
        DataFrame of customers.
        
    '''
    
    if nr_items <= 0:
        raise Exception("'nr_items' has to be larger than 0.")
    
    auth = login(config.CLIENT_ID, config.CLIENT_SECRET, config.PROJECT_KEY, 
                 config.SCOPE, config.HOST)
    
    cols = ['id', 'firstName', 'middleName', 'lastName', 'email', 
            'dateOfBirth', 'companyName', 
            'customerGroup_ids', 'customerGroup_names']
    df = pd.DataFrame(index=[], columns=cols)
    
    limit = nr_items if nr_items <= size_chunks else size_chunks
    
    while True:
        
        if verbose:
            print('Loading customers chunk (offset: {}, chunk size = {}, nr = {})'.format(offset, size_chunks, nr_items))
        
        endpoint = "customers?limit=%s&offset=%s"  % (limit, offset)
        data_json = query(endpoint, config.PROJECT_KEY, auth, config.HOST)
        
        df_chunk = pd.DataFrame(index=[], columns=cols)
        results = data_json['results']

        for i, customer in enumerate(results):
            
            # Mandatory fields
            df_chunk.loc[i, 'id'] = customer['id']
            df_chunk.loc[i, 'createdAt'] = customer['createdAt']

            # Optional fields
            try:
                df_chunk.loc[i, 'firstName'] = customer['firstName']
            except:
                df_chunk.loc[i, 'firstName'] = ''
                
            try:
                df_chunk.loc[i, 'lastName'] = customer['lastName']
            except:
                df_chunk.loc[i, 'lastName'] = ''
                
            try:
                df_chunk.loc[i, 'middleName'] = customer['middleName']
            except:
                df_chunk.loc[i, 'middleName'] = ''
                
            try:
                df_chunk.loc[i, 'email'] = customer['email']
            except:
                df_chunk.loc[i, 'email'] = ''
                
            try:
                df_chunk.loc[i, 'dateOfBirth'] = customer['dateOfBirth']
            except:
                df_chunk.loc[i, 'dateOfBirth'] = ''
                
            try:
                df_chunk.loc[i, 'companyName'] = customer['companyName']
            except:
                df_chunk.loc[i, 'companyName'] = ''
                
            
            # Customer groups
            try:
                groups_json = customer['customerGroup']
                groups_ids = []
                groups_names = []
                for group_json in groups_json:
                    try:
                        groups_ids.append(group_json['id'])
                    except:
                        None
                    try:
                        groups_names.append(group_json['name'])
                    except:
                        None
                df_chunk.loc[i, 'customerGroup_ids'] = groups_ids
                df_chunk.loc[i, 'customerGroup_names'] = groups_names
            except:
                df_chunk.loc[i, 'customerGroup_ids'] = ''
                df_chunk.loc[i, 'customerGroup_names'] = ''
            

        if nr_items <= size_chunks:
            
            df = df.append(df_chunk, ignore_index=True)
            return df
            
        else:
            
            nr_items -= size_chunks
            offset += size_chunks
            limit = nr_items if nr_items <= size_chunks else size_chunks
            df = df.append(df_chunk, ignore_index=True)

    
def orders(nr_items, offset=0, size_chunks = 250, languages=['en','de'], verbose=True):
    '''Queries the commercetools API to create a DataFrame of orders.
    
    Args:
        nr_items: Maximum number of retrieved items.
        offset: offset of retrieved items (i.e. offset=5 will omit the first 6 items).
        
    Returns:
        DataFrame of orders.
        
    '''
    
    if nr_items <= 0:
        raise Exception("'nr_items' has to be larger than 0.")
    
    auth = login(config.CLIENT_ID, config.CLIENT_SECRET, config.PROJECT_KEY, 
                 config.SCOPE, config.HOST)

    cols = ['productId','customerId','customerEmail','anonymousId','orderId',
            'createdAt','productPrice','totalPrice','currency','quantity',
            'country']
            
    # Language-dependent variables
    ld_vars = ['name']
    [cols.append(ld_var + '_' + language) for ld_var in ld_vars for language in languages]
    
    df = pd.DataFrame([], columns=cols)
    
    limit = nr_items if nr_items <= size_chunks else size_chunks
    
    while True:
        
        if verbose:
            print('Loading orders chunk (offset: {}, chunk size = {}, nr = {})'.format(offset, size_chunks, nr_items))
        
        endpoint = "orders?limit=%s&offset=%s"  % (limit, offset)
        data_json = query(endpoint, config.PROJECT_KEY, auth, config.HOST)
        results = data_json['results']
        nr_results = len(results)
        
        df_chunk = pd.DataFrame(np.zeros((nr_results, len(cols))), columns=cols)
        
        counter = 0
        
        for i, order in enumerate(results):
            
            nr_items = len(order['lineItems'])
            
            for j in range(nr_items):
                    
                # Mandatory fields
                df_chunk.loc[counter, 'orderId'] = order['id']
                df_chunk.loc[counter, 'productId'] = order['lineItems'][j]['productId']
                df_chunk.loc[counter, 'createdAt'] = order['createdAt']
                df_chunk.loc[counter, 'totalPrice'] = order['totalPrice']['centAmount']
                df_chunk.loc[counter, 'currency'] = order['totalPrice']['currencyCode']

                # Optional fields
                try:
                    df_chunk.loc[counter, 'customerId'] = order['customerId']
                except KeyError:
                    df_chunk.loc[counter, 'customerId'] = 'anonymous'
                    
                try:
                    df_chunk.loc[counter, 'customerEmail'] = order['customerEmail']
                except KeyError:
                    df_chunk.loc[counter, 'customerEmail'] = ''
                    
                try:
                    df_chunk.loc[counter, 'anonymousId'] = order['anonymousId']
                except KeyError:
                    df_chunk.loc[counter, 'anonymousId'] = ''
                    
                try:
                    df_chunk.loc[counter, 'country'] = order['country']
                except KeyError:
                    df_chunk.loc[counter, 'country'] = ''
                    
                try:
                    df_chunk.loc[counter, 'productPrice'] = order['lineItems'][j]['price']['value']['centAmount']
                except:
                    df_chunk.loc[counter, 'productPrice'] = ''
                    
                try:
                    df_chunk.loc[counter, 'currency'] = order['lineItems'][j]['price']['value']['currencyCode']
                except:
                    df_chunk.loc[counter, 'currency'] = ''
                    
                try:
                    df_chunk.loc[counter, 'quantity'] = order['lineItems'][j]['quantity']
                except:
                    df_chunk.loc[counter, 'quantity'] = ''
                    
                # Language-dependent variables
                for ld_var in ld_vars:
                    for language in languages:
                        var = ld_var + '_' + language
                        try:
                            df_chunk.loc[i, var] = order['lineItems'][j][ld_var][language]
                        except:
                            df_chunk.loc[i, var] = ''
                
                counter += 1

        if nr_items <= size_chunks:
            
            df = df.append(df_chunk, ignore_index=True)
            return df
            
        else:
            nr_items -= size_chunks
            offset += size_chunks
            limit = nr_items if nr_items <= size_chunks else size_chunks
            df = df.append(df_chunk, ignore_index=True)
            

def categories(nr_items, offset=0, size_chunks = 250, languages=['en','de'],
               verbose=True):
    '''Queries the commercetools API to create a DataFrame of categories.
    
    Args:
        nr_items: Maximum number of retrieved items.
        
    Returns:
        DataFrame of categories.
        
    '''

    if nr_items <= 0:
        raise Exception("nr_items has to be larger than 0.")
    
    auth = login(config.CLIENT_ID, config.CLIENT_SECRET, config.PROJECT_KEY, 
                 config.SCOPE, config.HOST)
    
    cols = ['id','createdAt']

    # Language-dependent variables
    ld_vars = ['name','slug','description']
    [cols.append(ld_var + '_' + language) for ld_var in ld_vars for language in languages]
    
    df = pd.DataFrame(index=[], columns=cols)
    limit = nr_items if nr_items <= size_chunks else size_chunks
    
    while True:
        
        if verbose:
            print('Loading categories chunk (offset: {}, chunk size = {}, nr = {})'.format(offset, size_chunks, nr_items))
        
        endpoint = "categories?limit=%s&offset=%s"  % (limit, offset)
        data_json = query(endpoint, config.PROJECT_KEY, auth, config.HOST)
        results = data_json['results']
        
        df_chunk = pd.DataFrame(index=[], columns=cols)

        for i, category in enumerate(results):
            
            # Mandatory fields
            df_chunk.loc[i, 'id'] = category['id']
            df_chunk.loc[i, 'createdAt'] = category['createdAt']
                    
            # Language-dependent variables
            for ld_var in ld_vars:
                for language in languages:
                    var = ld_var + '_' + language
                    try:
                        df_chunk.loc[i, var] = category[ld_var][language]
                    except:
                        df_chunk.loc[i, var] = ''
                

        if nr_items <= size_chunks:
            
            df = df.append(df_chunk, ignore_index=True)
            return df
            
        else:
            
            nr_items -= size_chunks
            offset += size_chunks
            limit = nr_items if nr_items <= size_chunks else size_chunks
            df = df.append(df_chunk, ignore_index=True)
            
