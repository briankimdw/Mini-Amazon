# app/inventory.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import current_user, login_required
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.seller_products import SellerProduct  # Ensure this model exists
from app.models.category import Category  # Ensure this model exists
from datetime import datetime
from .models.reviews import Reviews
from app.models.user import User
from app.models.order_items import OrderItem
from app.models.orders import Order

bp = Blueprint('seller', __name__, url_prefix='/seller')

@bp.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        product_ids = request.form.getlist('product_ids[]')
        quantities = request.form.getlist('quantities[]')
        for product_id, quantity in zip(product_ids, quantities):
            try:
                product_id = int(product_id)
                quantity = int(quantity)
                inventory = Inventory.get_by_product_and_seller(product_id, current_user.id)
                if inventory:
                    success = Inventory.update_quantity(inventory.inventory_id, quantity)
                    if not success:
                        flash(f'Failed to update inventory for product ID {product_id}.', 'danger')
                else:
                    inventory = Inventory.create_inventory(current_user.id, product_id, quantity)
                    if not inventory:
                        flash(f'Failed to create inventory for product ID {product_id}.', 'danger')
            except ValueError:
                flash(f'Invalid quantity for product ID {product_id}', 'danger')
                continue
        flash('Inventory updated successfully!', 'success')
        return redirect(url_for('profile.profile'))
    
    # GET request - display inventory
    products = Product.get_by_seller(current_user.id)
    inventory_list = Inventory.get_by_seller(current_user.id)
    inventory_dict = {inv.product_id: inv for inv in inventory_list}
    return render_template('seller_profile.html', title='Seller Inventory Data', products=products, inventory=inventory_dict)

@bp.route('/create_product', methods=['GET', 'POST'])
@login_required
def create_product():
    if request.method == 'POST':
        # Retrieve the last selected category_id
        category_ids = request.form.getlist('category_id')
        category_id = category_ids[-1] if category_ids else None
        # Existing code to handle product creation
        # Retrieve form data
        name = request.form.get('name')
        summary = request.form.get('summary')
        price = request.form.get('price')
        image_url = request.form.get('image_url')
        quantity = request.form.get('quantity')

        # Validate required fields
        if not name or not price or not category_id or not quantity:
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('seller.create_product'))

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            flash('Invalid input for price or quantity.', 'danger')
            return redirect(url_for('seller.create_product'))

        # Create the product
        new_product = Product.create(
            seller_id=current_user.id,
            category_id=category_id,
            name=name,
            summary=summary,
            image_url=image_url,
            price=price,
            available=True
        )

        if new_product:
            # Associate the product with the seller
            SellerProduct.add_seller_product(seller_id=current_user.id, product_id=new_product.product_id)

            # Create initial inventory
            Inventory.create_inventory(
                seller_id=current_user.id,
                product_id=new_product.product_id,
                quantity=quantity
            )

            flash('Product created successfully!', 'success')
            return redirect(url_for('seller.inventory'))
        else:
            flash('An error occurred while creating the product.', 'danger')
            return redirect(url_for('seller.create_product'))
    else:
        # Existing code for GET request
        # For GET request, fetch categories to populate dropdown
        categories = Category.get_all()
        # Retrieve form data from session if available
        form_data = session.pop('create_product_form_data', {})
        return render_template('create_product.html', title='List a New Product', categories=categories, form_data=form_data)

@bp.route('/seller_products', methods=['GET'])
@login_required
def seller_products():
    if not current_user.is_seller:
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('profile.profile'))

    products = Product.get_by_seller(current_user.id)
    return render_template('seller_products.html', products=products)

@bp.route('/product_reviews/<int:product_id>', methods=['GET'])
@login_required
def product_reviews(product_id):
    product = Product.get(product_id)
    if not product or product.seller_id != current_user.id:
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('seller.seller_products'))

    reviews = Reviews.get_by_product(product_id)
    # Fetch reviewer details
    for review in reviews:
        reviewer = User.get(review.reviewer_id)
        review.reviewer = reviewer
    return render_template('product_reviews.html', product=product, reviews=reviews)

@bp.route('/order_fulfillment/<int:product_id>', methods=['GET', 'POST'])
@login_required
def order_fulfillment(product_id):
    if not current_user.is_seller:
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('profile.profile'))

    product = Product.get(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('seller.seller_products'))

    # Get unfulfilled order items for this product sold by the current seller
    order_items = OrderItem.get_unfulfilled_order_items_by_seller_and_product(current_user.id, product_id)

    # Fetch buyer information for each order item
    for item in order_items:
        order = Order.get(item.order_id)
        buyer = User.get(order.user_id)
        item.buyer = buyer

    if request.method == 'POST':
        # Process form data to mark selected orders as fulfilled
        fulfilled_order_item_ids = request.form.getlist('fulfill_order_items')
        for order_item_id in fulfilled_order_item_ids:
            OrderItem.update_status(order_item_id, 'Fulfilled')
        flash('Selected orders have been marked as fulfilled.', 'success')
        return redirect(url_for('seller.order_fulfillment', product_id=product_id))

    return render_template('fulfillment.html', product=product, order_items=order_items)

# app/models/inventory.py
@staticmethod
def get_by_product_and_seller(product_id, seller_id):
    rows = app.db.execute('''
SELECT inventory_id, seller_id, product_id, quantity, updated_at
FROM Inventory
WHERE product_id = :product_id AND seller_id = :seller_id
LIMIT 1
''', product_id=product_id, seller_id=seller_id)
    return Inventory(*rows[0]) if rows else None
