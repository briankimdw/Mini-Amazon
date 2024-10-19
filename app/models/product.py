from flask import current_app as app

class Product:
    def __init__(self, id, seller_id, category_id, name, summary, image_url, price, created_at, updated_at, available):
        self.id = id
        self.seller_id = seller_id
        self.category_id = category_id
        self.name = name
        self.summary = summary
        self.image_url = image_url
        self.price = price
        self.created_at = created_at
        self.updated_at = updated_at
        self.available = available

    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT product_id, seller_id, category_id, name, summary, image_url, price, created_at, updated_at, available
FROM Products
WHERE product_id = :id
''',
                              id=id)
        return Product(*(rows[0])) if rows else None

    @staticmethod
    def get_all(available=True):
        rows = app.db.execute('''
SELECT product_id, seller_id, category_id, name, summary, image_url, price, created_at, updated_at, available
FROM Products
WHERE available = :available
''',
                              available=available)
        return [Product(*row) for row in rows]

    @staticmethod
    def get_by_seller(seller_id):
        rows = app.db.execute('''
SELECT product_id, seller_id, category_id, name, summary, image_url, price, created_at, updated_at, available
FROM Products
WHERE seller_id = :seller_id
''',
                              seller_id=seller_id)
        return [Product(*row) for row in rows]

    @staticmethod
    def get_by_category(category_id):
        rows = app.db.execute('''
SELECT product_id, seller_id, category_id, name, summary, image_url, price, created_at, updated_at, available
FROM Products
WHERE category_id = :category_id
''',
                              category_id=category_id)
        return [Product(*row) for row in rows]
