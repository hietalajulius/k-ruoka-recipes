from requests.auth import AuthBase
import requests
import json

class KAuth(AuthBase):
    def __init__(self, key):
        self.key = key

    def __call__(self, r):
        r.headers['Ocp-Apim-Subscription-Key'] = self.key
        r.headers['Content-Type'] = 'application/json'
        return r

def get_recipe(recipe_id, main_category="4", sub_category="28"):
    recipe_url = 'https://kesko.azure-api.net/v1/search/recipes'
    key = "6f9320c4ee544173af84a9e0b561bf0a"
    body = {'filters' : {'mainCategory': main_category, 'subCategory': sub_category}}
    recipes_response = requests.post(recipe_url, json=body, auth=KAuth(key))
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
        parsed_ingredient = {}
        parsed_ingredient['name'] = ingredient[0]['IngredientTypeName']
        parsed_ingredient['amount'] = ingredient[0]['Amount']
        parsed_ingredient['unit'] = ingredient[0]['Unit']
        parsed_ingredient['type'] = ingredient[0]['IngredientType']
        parsed_ingredients.append(parsed_ingredient)
    return parsed_ingredients
    
def get_items_for_item_type(item_type):
    products_url = 'https://kesko.azure-api.net/v1/search/products'
    key = "6f9320c4ee544173af84a9e0b561bf0a"
    body = {'filters' : {'ingredientType': item_type}}
    items_response = requests.post(products_url, json=body, auth=KAuth(key))
    items_json = json.loads(items_response.text)
    return items_json['results']

def parse_items(items):
    parsed_items = []
    for item in items:
        parsed_item = {}
        parsed_item['ean'] = item['ean']
        parsed_item['name'] = item['labelName']['english']
        parsed_items.append(parsed_item)
    return parsed_items

def get_stores(zip_code = '00180'):
    store_url = 'https://kesko.azure-api.net/v1/search/stores'
    body = {'filters' : {'postCode': zip_code}}
    stores_response = requests.post(store_url, json=body, auth=KAuth(key))
    stores_json = json.loads(stores_response.text)
    return stores_json['results']

def parse_stores(stores):
    parsed_stores = []
    for store in stores:
        parsed_store = {}
        parsed_store['name'] = store['Name']
        parsed_store['id'] = store['Id']
        parsed_stores.append(parsed_store)
    return parsed_stores

def check_availability(ean, store):
    key = "6f9320c4ee544173af84a9e0b561bf0a"
    availability_url = 'https://kesko.azure-api.net/v2/products?ean=' + ean
    availability_response = requests.get(availability_url, auth=KAuth(key))
    availability_json = json.loads(availability_response.text)
    availability_stores = availability_json[0]['stores']
    for a_store in availability_stores:
        if a_store['id'] == store['id']:
            return True
    return False
