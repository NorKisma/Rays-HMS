from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.extensions import db
from . import bp
from app.models import Category, Product, Batch, Inventory, StockLog
import pandas as pd
from datetime import datetime
from .forms import CategoryForm, ProductForm, BatchForm, ImportInventoryForm

@bp.route('/')
@login_required
@permission_required('view_inventory')
def index():
    items = Inventory.query.join(Product).filter(Inventory.is_deleted == False).all()
    return render_template('inventory/index.html', items=items)

@bp.route('/product/add', methods=['GET', 'POST'])
@login_required
@permission_required('add_inventory')
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_deleted=False).all()]
    if form.validate_on_submit():
        product = Product()
        form.populate_obj(product)
        db.session.add(product)
        db.session.commit()
        flash('Product added to catalog!', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/create_product.html', form=form, title="Add New Product")

@bp.route('/batch/add', methods=['GET', 'POST'])
@login_required
@permission_required('adjust_stock')
def add_batch():
    form = BatchForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.filter_by(is_deleted=False).all()]
    if form.validate_on_submit():
        batch = Batch(
            product_id=form.product_id.data,
            batch_number=form.batch_number.data,
            expiry_date=form.expiry_date.data,
            unit_cost=form.unit_cost.data,
            selling_price=form.selling_price.data
        )
        db.session.add(batch)
        db.session.flush() # get batch id
        
        # Update or Create Inventory entry
        inv = Inventory.query.filter_by(product_id=batch.product_id, batch_id=batch.id).first()
        if not inv:
            inv = Inventory(product_id=batch.product_id, batch_id=batch.id, quantity=0)
            db.session.add(inv)
        
        # Get product to access its base_unit
        product = Product.query.get(batch.product_id)
        old_qty = inv.quantity
        inv.quantity += form.quantity.data
        if product:
            inv.unit = product.base_unit
        
        # Log stock change
        log = StockLog(
            product_id=batch.product_id,
            batch_id=batch.id,
            change_type='Purchase',
            old_qty=old_qty,
            new_qty=inv.quantity,
            difference=form.quantity.data,
            user_id=current_user.id,
            note=f"Manual batch addition: {batch.batch_number}"
        )
        db.session.add(log)
        db.session.commit()
        flash('Stock batch added successfully!', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/create_batch.html', form=form, title="Add Stock Batch")

@bp.route('/categories', methods=['GET', 'POST'])
@login_required
@permission_required('add_inventory')
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data, description=form.description.data)
        db.session.add(cat)
        db.session.commit()
        flash('Category created!', 'success')
        return redirect(url_for('inventory.categories'))
    categories = Category.query.filter_by(is_deleted=False).all()
    return render_template('inventory/categories.html', categories=categories, form=form)

@bp.route('/import', methods=['GET', 'POST'])
@login_required
@permission_required('add_inventory')
def import_inventory():
    form = ImportInventoryForm()
    if form.validate_on_submit():
        file = form.import_file.data
        filename = file.filename
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Debug: Print columns found
            print(f"DEBUG: Columns in file: {list(df.columns)}")

            # Normalize Headers: lowercase and strip
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Helper to find column matching a list of potential names
            def get_col(candidates):
                for c in candidates:
                    if c.lower() in df.columns:
                        return c.lower()
                return None

            # Map inputs to possible columns
            col_map = {
                'name': get_col(['product name', 'product', 'name', 'item', 'description']),
                'category': get_col(['category', 'cat', 'group', 'type']),
                'barcode': get_col(['barcode', 'sku', 'code', 'id']),
                'batch': get_col(['batch number', 'batch', 'lot', 'serial']),
                'expiry': get_col(['expiry date', 'expiry', 'exp', 'expiration']),
                'qty': get_col(['quantity', 'qty', 'count', 'amount', 'stock']),
                'cost': get_col(['unit cost', 'cost', 'buy price', 'purchase price']),
                'price': get_col(['selling price', 'price', 'sell price', 'rate'])
            }

            print(f"DEBUG: Column Mapping: {col_map}")

            if not col_map['name']:
                flash('Error: Could not find a "Product Name" column in file.', 'danger')
                return redirect(url_for('inventory.import_inventory'))
            
            success_count = 0
            
            for index, row in df.iterrows():
                # Extract Data safely using mapped columns
                p_name_raw = row.get(col_map['name'], '')
                p_name = str(p_name_raw).strip() if pd.notna(p_name_raw) else ''
                
                c_col = col_map.get('category')
                c_name_raw = row.get(c_col, 'Uncategorized') if c_col else 'Uncategorized'
                c_name = str(c_name_raw).strip() if pd.notna(c_name_raw) else 'Uncategorized'
                
                b_col = col_map.get('barcode')
                barcode_raw = row.get(b_col, '') if b_col else ''
                barcode = str(barcode_raw).strip() if pd.notna(barcode_raw) and str(barcode_raw).lower() != 'nan' else None
                
                bat_col = col_map.get('batch')
                batch_num_raw = row.get(bat_col, '') if bat_col else ''
                batch_num = str(batch_num_raw).strip() if pd.notna(batch_num_raw) and str(batch_num_raw).lower() != 'nan' else f"BATCH-{int(datetime.utcnow().timestamp())}-{index}"
                
                q_col = col_map.get('qty')
                qty = float(row.get(q_col, 0)) if q_col and pd.notna(row.get(q_col, 0)) else 0.0

                cost_col = col_map.get('cost')
                cost = float(row.get(cost_col, 0)) if cost_col and pd.notna(row.get(cost_col, 0)) else 0.0

                price_col = col_map.get('price')
                price = float(row.get(price_col, 0)) if price_col and pd.notna(row.get(price_col, 0)) else 0.0
                
                exp_col = col_map.get('expiry')
                expiry_str = str(row.get(exp_col, '')) if exp_col else ''
                try:
                    expiry = pd.to_datetime(expiry_str).date()
                except:
                    expiry = None

                if not p_name:
                    continue

                # 1. Get or Create Category
                category = Category.query.filter_by(name=c_name).first()
                if not category:
                    category = Category(name=c_name)
                    db.session.add(category)
                    db.session.flush()
                
                # 2. Get or Create Product
                product = Product.query.filter_by(name=p_name).first()
                if not product:
                    product = Product(
                        name=p_name,
                        category_id=category.id,
                        barcode=barcode,
                        base_unit="Unit"
                    )
                    db.session.add(product)
                    db.session.flush()
                
                # 3. Create Batch
                batch = Batch(
                    product_id=product.id,
                    batch_number=batch_num,
                    expiry_date=expiry,
                    unit_cost=cost,
                    selling_price=price,
                    status='active'
                )
                db.session.add(batch)
                db.session.flush()
                
                # 4. Create/Update Inventory
                inv = Inventory.query.filter_by(product_id=product.id, batch_id=batch.id).first()
                if not inv:
                    inv = Inventory(product_id=product.id, batch_id=batch.id, quantity=0, unit=product.base_unit)
                    db.session.add(inv)
                
                old_qty = inv.quantity
                inv.quantity += qty
                
                # 5. Log Stock
                log = StockLog(
                    product_id=product.id,
                    batch_id=batch.id,
                    change_type='Import',
                    old_qty=old_qty,
                    new_qty=inv.quantity,
                    difference=qty,
                    user_id=current_user.id,
                    note=f"Bulk Import: {filename}"
                )
                db.session.add(log)
                success_count += 1
                
            db.session.commit()
            flash(f'Successfully imported {success_count} items from {filename}', 'success')
            return redirect(url_for('inventory.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('inventory.import_inventory'))
            
    return render_template('inventory/import.html', form=form)

@bp.route('/alerts')
@login_required
def alerts():
    from datetime import date, timedelta
    
    # Low Stock Items (Quantity <= 10)
    low_stock = Inventory.query.join(Product).filter(
        Inventory.quantity <= 10,
        Inventory.is_deleted == False
    ).all()
    
    # Expiring Soon (Next 90 days)
    today = date.today()
    ninety_days = today + timedelta(days=90)
    expiring_batches = Batch.query.join(Product).filter(
        Batch.expiry_date.between(today, ninety_days),
        Batch.is_deleted == False
    ).order_by(Batch.expiry_date.asc()).all()
    
    # Already Expired
    expired_batches = Batch.query.join(Product).filter(
        Batch.expiry_date < today,
        Batch.is_deleted == False
    ).order_by(Batch.expiry_date.desc()).all()
    
    return render_template('inventory/alerts.html', 
                           low_stock=low_stock, 
                           expiring=expiring_batches, 
                           expired=expired_batches,
                           today=today)
