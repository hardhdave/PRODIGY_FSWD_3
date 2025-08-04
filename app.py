from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Product, CartItem, Order, OrderItem
from forms import CheckoutForm
from config import Config
import uuid
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Create session ID if not exists
def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

@app.route('/')
def index():
    # Get all products for homepage
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    session_id = get_session_id()
    product = Product.query.get_or_404(product_id)
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(
        session_id=session_id, 
        product_id=product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(
            session_id=session_id,
            product_id=product_id,
            quantity=1
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    session_id = get_session_id()
    cart_items = CartItem.query.filter_by(session_id=session_id).all()
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove_from_cart/<int:cart_item_id>')
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:cart_item_id>', methods=['POST'])
def update_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        db.session.commit()
        flash('Cart updated!', 'success')
    else:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart!', 'success')
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    session_id = get_session_id()
    cart_items = CartItem.query.filter_by(session_id=session_id).all()
    
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))
    
    form = CheckoutForm()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    if form.validate_on_submit():
        # Create order
        order = Order(
            customer_name=form.customer_name.data,
            customer_email=form.customer_email.data,
            customer_phone=form.customer_phone.data,
            address=form.address.data,
            total_amount=total
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
        
        # Clear cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        db.session.commit()
        flash(f'Order #{order.id} placed successfully!', 'success')
        return redirect(url_for('order_success', order_id=order.id))
    
    return render_template('checkout.html', form=form, cart_items=cart_items, total=total)

@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('order_success.html', order=order)

# Create database tables and add sample data
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Add sample products if none exist
        if Product.query.count() == 0:
            sample_products = [
                Product(
                    name='Laptop', 
                    description='High-performance laptop perfect for work and gaming', 
                    price=999.99, 
                    stock=10, 
                    category='Electronics',
                    image_url='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&h=300&fit=crop'
                ),
                Product(
                    name='Smartphone', 
                    description='Latest smartphone with advanced camera and features', 
                    price=699.99, 
                    stock=15, 
                    category='Electronics',
                    image_url='https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop'
                ),
                Product(
                    name='Headphones', 
                    description='Noise-canceling wireless headphones with premium sound', 
                    price=199.99, 
                    stock=20, 
                    category='Electronics',
                    image_url='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop'
                ),
                Product(
                    name='T-Shirt', 
                    description='Comfortable cotton t-shirt in various colors', 
                    price=29.99, 
                    stock=50, 
                    category='Clothing',
                    image_url='https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=300&fit=crop'
                ),
                Product(
                    name='Jeans', 
                    description='Classic denim jeans with perfect fit and comfort', 
                    price=79.99, 
                    stock=30, 
                    category='Clothing',
                    image_url='https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=300&fit=crop'
                )
            ]
            
            for product in sample_products:
                db.session.add(product)
            
            db.session.commit()
            print("Sample products added to database!")

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
