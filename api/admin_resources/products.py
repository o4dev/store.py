from flask import request

from ..utils import check_data, Resource
from ..resources.products import (Products, Product, ProductImage,
                                  Categories, pass_product)
from ..resources.products import models


def valid_file(image):
    return image.content_type == 'image/jpeg'


class ProductsAdmin(Products):
    def get(self):
        return models.Product.find()

    def post(self):
        REQUIRED = [
            'desciption',
            'cost', 'name'
        ]
        data = request.get_json(force=True)

        # Check product data.
        allowed, resp = check_data(data, REQUIRED, True)
        if not allowed:
            return resp

        data['recipes'] = []
        data['stock'] = 0
        data['active'] = False

        product = models.product.new(**data)
        return product


class ProductAdmin(Product):
    def get(self, product):
        return product

    def put(self, product):
        ALLOWED = [
            'description', 'cost',
            'name', 'recipes', 'category_ids',
            'active', 'stock',

            '$inc'
        ]
        RECIPE_REQUIRED = [
            'name', 'url'
        ]
        data = request.get_json(force=True)
        # Check product data.
        allowed, resp = check_data(data, ALLOWED)
        if not allowed:
            return resp

        # Check recipe data.
        if 'recipes' in data and len(data['recipes']):
            for recipe in data['recipes']:
                allowed, resp = check_data(recipe,
                                           RECIPE_REQUIRED, True)
                if not allowed:
                    return resp

        if 'category_ids' in data:
            product.categories = data['category_ids']
            del data['category_ids']

        if 'stock' in data:
            data['stock'] = int(data['stock'])

        kwargs = {}
        if '$inc' in data and data['$inc']:
            del data['$inc']
            kwargs['_inc'] = data
        else:
            kwargs['_set'] = data

        if data:
            res = product.update(**kwargs)
            if not res['nModified']:
                return "SEVER ERROR; not modified.", 500

        return product


class ProductImageAdmin(Resource):
    decorators = [pass_product]

    def post(self, product, image_index):
        for file in request.files:
            if not valid_file(file):
                return 400
            product.add_image(file)

        return product

    def put(self, product, image_index):
        if image_index > len(product['images']):
            return "NOT FOUND; image does not exist", 404

        file = request.files['file']
        if not valid_file(file):
            return 400

        file = file.stream.read()
        if image_index == len(product['images']):
            image_index = None
        product.add_image(file, image_index)

        return product

    def delete(self, product, image_index):
        if image_index >= len(product['images']):
            return "NOT FOUND; image does not exist", 404

        del product['images'][image_index]
        product.update()


def register_resources(admin_api):
    admin_api.add_resource(ProductsAdmin, '/products')
    admin_api.add_resource(Categories, '/categories')

    admin_api.add_resource(ProductAdmin, '/products/<ObjectID:id>')
    admin_api.add_resource(
        ProductImageAdmin,
        '/products/<ObjectID:id>/<int:image_index>'
    )