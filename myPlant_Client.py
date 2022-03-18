import json
import os
import random
import time
from datetime import datetime
from multiprocessing import Pool
from pprint import pprint

import pandas as pd
import requests
import urllib3


class myPlant_Client:
    def __init__(
            self,
            user='JQHTKP1T496PG',
            password='ae0874a64b659fea0af47e1f5c72f2dc',
            max_limit=100000,
    ):
        self.__version__ = '0.1.0'
        self.user = user
        self.password = password
        self.max_limit = max_limit
        self.proxies = None

        # Disable insecure ssl request warning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_access_token(self):
        """TODO: get access token only with first request"""
        url = 'https://web.myplant.io/api/oauth/token'
        auth = (self.user, self.password)
        data = {'grant_type': 'client_credentials'}

        r = requests.post(url, auth=auth, data=data,
                          verify=False, proxies=self.proxies)
        self.access_token = r.json()['access_token']

    def get_assets(self, filters=None):
        """Downloads all assets"""
        r = self._request_assets(filters=filters)
        if r.status_code != 200:
            print(r.text)
            return False

        assets = self._flatten_assets(r)
        assets.rename(columns={'id': 'assetId'}, inplace=True)
        assert len(assets) < self.max_limit
        return assets

    def get_properties(self):
        """Downloads all properties"""
        url = 'https://web.myplant.io/api/modelproperty'
        headers = {'x-seshat-token': self.access_token}
        params = {
        }
        r = requests.get(url, headers=headers, params=params,
                         verify=False, proxies=self.proxies)
        if r.status_code != 200:
            print(r.text)
            return False

        properties = pd.DataFrame(r.json())
        assert len(properties) < self.max_limit
        return properties

    def get_dataItems(self):
        """Downloads all dataItems"""
        url = 'https://web.myplant.io/api/dataitem'
        headers = {'x-seshat-token': self.access_token}
        params = {
        }
        r = requests.get(url, headers=headers, params=params,
                         verify=False, proxies=self.proxies)
        if r.status_code != 200:
            print(r.text)
            return False

        dataItems = pd.DataFrame(r.json())
        assert len(dataItems) < self.max_limit
        return dataItems

    def _request_assets(self, limit=None, filters=None):
        # TODO:
        #   - make properties and dataItems as parameters with default vals
        #   - add modelId filter
        #   - add historic dataItem query with aggregate?
        if not limit:
            limit = self.max_limit
        if not filters:
            filters = []

        # graphQL querry
        graphQL = """
        {
        assets(
            filter: {
                limit: %s
                filters: [
        	       %s
                ]
            }
        ) {
          items {
            id
            serialNumber
            modelId
            model
            site {
              name
              country
            }
            customer {
              name
            }
            geoLocation {
              lat
              lon
            }
            properties(names: [
              "Engine Series",
              "Engine Type",
              "Engine Version",
              "Customer Engine Number",
              "Design Number",
              "Gas Type",
              "Commissioning Date"
              "Contract.Service Contract Type"
            ]) {
              name
              value
            }
            dataItems(query: [
              "OperationalCondition",
              "Count_OpHour",
              "Count_Start",
              "Power_PowerNominal",
              "Issue_Eng_OpHour",
              "Para_Engine_Power_FastStart_GEN2_preM_Act"
            ]) {
              name
              value
              unit
              timestamp
            }
          }
        }
        }
        """ % (limit, ','.join(filters))
        # Post request
        url = 'https://web.myplant.io/api/graphql'
        headers = {'x-seshat-token': self.access_token}
        r = requests.post(url, headers=headers, json={
                          'query': graphQL}, verify=False, proxies=self.proxies)
        return r

    def _flatten_assets(self, r):
        # Convert response to flat table
        assets_list = []
        for asset in r.json()['data']['assets']['items']:
            asset_dict = {}
            for item, item_value in asset.items():
                if type(item_value) is dict:
                    for key, value in item_value.items():
                        asset_dict[item + '_' + key] = item_value[key]
                elif type(item_value) is list:
                    for sub_item in item_value:
                        asset_dict[sub_item['name']] = sub_item['value']
                elif item_value is None:
                    pass
                else:
                    asset_dict[item] = asset[item]
            assets_list.append(asset_dict)
        assets = pd.DataFrame(assets_list)
        cols_to_begin = [
            'id', 'serialNumber', 'customer_name', 'site_name', 'Customer Engine Number', 'site_country',
            'Engine Type', 'OperationalCondition', 'model', 'modelId',
        ]
        assets = df_move_cols_to_begin(assets, cols_to_begin)
        return assets


def df_move_cols_to_begin(df, cols_at_begin):
    """Helper function to reorder columns in a dataframe"""
    return df[[c for c in cols_at_begin if c in df] + [c for c in df if c not in cols_at_begin]]


# Code for testing
if __name__ == '__main__':
    # Init client
    client = myPlant_Client()
    client.get_access_token()

    # Download assets
    assets = client.get_assets()
    print(assets.head())
    assets.to_csv('assets.csv')

    # Download properties
    properties = client.get_properties()
    print(properties.head())
    properties.to_csv('properties.csv')

    # Download properties
    dataItems = client.get_dataItems()
    print(dataItems.head())
    dataItems.to_csv('dataItems.csv')
