from flask import Flask, render_template, redirect, url_for, request, session, flash
from models import db, User, Product
from forms import RegisterForm, LoginForm, ProductForm

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def create_tables():
    db.create_all()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash('User registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, password=form.password.data).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Logged in successfully!')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'seller':
                return redirect(url_for('seller_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('dashboard_admin.html')

@app.route('/customer/dashboard')
def customer_dashboard():
    if session.get('role') != 'customer':
        return redirect(url_for('login'))
    return render_template('dashboard_customer.html')

# ---------- SELLER PRODUCT MANAGEMENT ----------
@app.route('/seller/dashboard')
def seller_dashboard():
    if session.get('role') != 'seller':
        return redirect(url_for('login'))
    seller_id = session.get('user_id')
    products = Product.query.filter_by(seller_id=seller_id).all()
    return render_template('seller/dashboard.html', products=products)

@app.route('/seller/add', methods=['GET', 'POST'])
def add_product():
    if session.get('role') != 'seller':
        return redirect(url_for('login'))
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(name=form.name.data, price=float(form.price.data), seller_id=session['user_id'])
        db.session.add(product)
        db.session.commit()
        flash("Product added!")
        return redirect(url_for('seller_dashboard'))
    return render_template('seller/add_product.html', form=form)

@app.route('/seller/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if session.get('role') != 'seller':
        return redirect(url_for('login'))
    product = Product.query.get_or_404(product_id)
    if product.seller_id != session['user_id']:
        flash("Unauthorized")
        return redirect(url_for('seller_dashboard'))
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.price = float(form.price.data)
        db.session.commit()
        flash("Product updated!")
        return redirect(url_for('seller_dashboard'))
    return render_template('seller/edit_product.html', form=form)

@app.route('/seller/delete/<int:product_id>')
def delete_product(product_id):
    if session.get('role') != 'seller':
        return redirect(url_for('login'))
    product = Product.query.get_or_404(product_id)
    if product.seller_id != session['user_id']:
        flash("Unauthorized")
        return redirect(url_for('seller_dashboard'))
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.")
    return redirect(url_for('seller_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

