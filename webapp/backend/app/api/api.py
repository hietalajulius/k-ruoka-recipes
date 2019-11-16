from requests.auth import AuthBase
from config import KESKOConfig
import requests
import json
import random
import numpy as np
from app.inference.classifier import Classifier
import torch


class KAuth(AuthBase):
    def __init__(self):
        self.key = KESKOConfig.KESKO_PRIMARY_KEY

    def __call__(self, r):
        r.headers['Ocp-Apim-Subscription-Key'] = self.key
        r.headers['Content-Type'] = 'application/json'
        return r


def get_recipe(recipe_id, main_category="4", sub_category="28"):
    recipe_url = KESKOConfig.RECIPES_URL
    body = {'filters' : {'mainCategory': main_category, 'subCategory': sub_category}}
    recipes_response = requests.post(recipe_url, json=body, auth=KAuth())
    recipes_response_text = recipes_response.text
    recipes_response_json = json.loads(recipes_response_text)
    recipe = recipes_response_json['results'][recipe_id]
    name = recipe['Name']
    instructions = recipe['Instructions']
    ingredients = recipe['Ingredients'][0]['SubSectionIngredients']
    image = recipe['PictureUrls'][0]['Normal']
    return name, ingredients, instructions, image


def parse_ingredients(ingredients):
    parsed_ingredients = []
    for ingredient in ingredients:
        parsed_ingredient = {'name': ingredient[0]['IngredientTypeName'],
                             'amount': ingredient[0]['Amount'],
                             'unit': ingredient[0]['Unit'],
                             'type': ingredient[0]['IngredientType']
                             }
        parsed_ingredients.append(parsed_ingredient)
    return parsed_ingredients


def get_items_for_item_type(item_type):
    products_url = KESKOConfig.PRODUCTS_URL
    body = {'filters': {'ingredientType': item_type}}
    items_response = requests.post(products_url, json=body, auth=KAuth())
    items_json = json.loads(items_response.text)
    return items_json['results']


def parse_items(items):
    parsed_items = []
    for item in items:
        parsed_item = {'ean': item['ean'], 'name': item['labelName']['english']}
        parsed_items.append(parsed_item)
    return parsed_items


def get_stores(zip_code='00180'):
    store_url = KESKOConfig.STORES_URL
    body = {'filters': {'postCode': zip_code}}
    stores_response = requests.post(store_url, json=body, auth=KAuth())
    stores_json = json.loads(stores_response.text)
    return stores_json['results']


def parse_stores(stores):
    parsed_stores = []
    for store in stores:
        parsed_store = {'name': store['Name'],
                        'id': store['Id'],
                        'address': store['Address'],
                        'opening_hours': store['OpeningHours'][0]
                        }
        parsed_stores.append(parsed_store)
    return parsed_stores


def stores_output(zipcode):
    stores = get_stores(zipcode)
    stores_output = parse_stores(stores)
    return stores_output


def request_availability(ean):
    params = {'ean': ean}
    availability_response = requests.get(KESKOConfig.PRODUCTS_URL_V2, params=params, auth=KAuth())
    availability_json = json.loads(availability_response.text)
    availability_stores = availability_json[0]['stores']
    return availability_stores

def default_items():
    items = ['5286', '7191', '6807', '6932', '7532', '8116', '6269', '6751', '6517']
    item_dicts = []
    for item in items:
        item_dict = {}
        item_dict['id'] = item
        item_dict['name'] = "dummy name" #Get this from DB
        item_dict['image_url'] = "dummy.png" #Get this from DB
        item_dicts.append(item_dict)
    return item_dicts


def check_availability(availability_stores, store):
    for a_store in availability_stores:
        if a_store['id'] == store['id']:
            return True
        return False


def is_product_available(ean, store):
    availability_stores = request_availability(ean)
    return check_availability(availability_stores, store)

def infer_recipes(items=None, count=5):
    if items:
        items = items.split(',')
    else:
        items = [np.random.randint(0,7000)]
    classifier = Classifier()
    classifier.load_trained()
    suggestions = []
    for _ in range(count):
        if len(items) == 1:
            length = 1
        else:
            length = np.random.choice(range(1,len(items)))
        infer_items = random.sample(items, length)
        items_tensor = classifier.mangle_list_of_items_to_tensor(items)
        classifier.init_hidden(1)
        prediction = classifier(items_tensor, torch.tensor([len(items)]))
        max_ = int(prediction.detach().numpy().argmax(axis=2)[0][0]) #This is the order_id!
        suggestions.append(max_) #Add metadata to recipe once available in DB

    return np.unique(suggestions).tolist()



def get_rich_recipe(zip_code, recipe_id, existing_ingredient_types):
    stores = parse_stores(get_stores(zip_code))
    recipe_name, recipe_ingredients, recipe_instructions, recipe_image = get_recipe(recipe_id) #Get from DB
    parsed_ingredients = parse_ingredients(recipe_ingredients)
    rich_ingredients = []
    for ingredient in parsed_ingredients:
        available_in_store = 0
        available_store_name = 'none'
        own = 0
        if not ingredient['type'] in existing_ingredient_types:
            items = parse_items(get_items_for_item_type(ingredient['type']))
            for item in items:
                for store in stores:
                    if is_product_available(item['ean'], store):
                        available_in_store = 1
                        available_store_name = store['name']
        else:
            own = 1
            
        ingredient['availability'] = available_in_store
        ingredient['available_store_name'] = available_store_name
        ingredient['own'] = own
        rich_ingredients.append(ingredient)
    return recipe_name, rich_ingredients, recipe_instructions, recipe_image
