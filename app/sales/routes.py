import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from . import bp
from app.models import Product, Batch, Inventory, Sale, SaleItem, Patient, StockLog, Account, JournalEntry, JournalItem
from app.decorators import permission_required

@bp.route('/pos')
@login_required
@permission_required('view_sales') # Or specific POS permission
def pos():
    """Main POS Interface."""
    return render_template('sales/pos.html', title="Point of Sale")

@bp.route('/search-products')
@login_required
def search_products():
    """Live search for products in POS."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    # Find products with available stock
    # Join with Inventory and Batch to show available quantities
    results = db.session.query(Product, Inventory, Batch)\
        .join(Inventory, Product.id == Inventory.product_id)\
        .join(Batch, Inventory.batch_id == Batch.id)\
        .filter(Product.name.ilike(f'%{query}%'))\
        .filter(Inventory.quantity > 0)\
        .filter(Inventory.is_deleted == False).all()

    data = []
    for product, inv, batch in results:
        data.append({
            'id': product.id,
            'name': product.name,
            'batch_id': batch.id,
            'batch_number': batch.batch_number,
            'expiry': batch.expiry_date.strftime('%Y-%m-%d') if batch.expiry_date else 'No Expiry',
            'price': batch.selling_price,
            'stock': inv.quantity,
            'unit': inv.unit or 'unit'
        })
    return jsonify(data)

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Process a sale transaction."""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'status': 'error', 'message': 'No items in cart'}), 400

        cart_items = data['items']
        customer_name = data.get('customer_name', 'Walk-in Customer')
        payment_method = data.get('payment_method', 'Cash')
        discount = float(data.get('discount', 0))

        # 1. Generate Invoice Number
        # Simplified: INV-YYYYMMDD-ID
        today = datetime.now().strftime('%Y%m%d')
        last_sale = Sale.query.filter(Sale.invoice_number.like(f'INV-{today}-%')).order_by(Sale.id.desc()).first()
        if last_sale:
            last_id = int(last_sale.invoice_number.split('-')[-1])
            new_id = last_id + 1
        else:
            new_id = 1
        invoice_num = f"INV-{today}-{new_id:04d}"

        # 2. Create Sale Record
        new_sale = Sale(
            invoice_number=invoice_num,
            customer_name=customer_name,
            payment_method=payment_method,
            discount=discount,
            user_id=current_user.id,
            status='completed'
        )
        db.session.add(new_sale)
        db.session.flush() # Get ID

        total_amount = 0

        # 3. Process Items and Stock
        for item in cart_items:
            product_id = item['product_id']
            batch_id = item['batch_id']
            qty = float(item['quantity'])
            price = float(item['price'])
            subtotal = qty * price
            total_amount += subtotal

            # Verify stock
            inv = Inventory.query.filter_by(product_id=product_id, batch_id=batch_id).first()
            if not inv or inv.quantity < qty:
                db.session.rollback()
                return jsonify({'status': 'error', 'message': f'Insufficient stock for Product ID {product_id}'}), 400

            # Create SaleItem
            sale_item = SaleItem(
                sale_id=new_sale.id,
                product_id=product_id,
                batch_id=batch_id,
                quantity=qty,
                unit_price=price,
                subtotal=subtotal
            )
            db.session.add(sale_item)

            # Deduct stock
            old_qty = inv.quantity
            inv.quantity -= qty
            
            # Log stock movement
            log = StockLog(
                product_id=product_id,
                batch_id=batch_id,
                change_type='Sale',
                old_qty=old_qty,
                new_qty=inv.quantity,
                difference=-qty,
                user_id=current_user.id,
                note=f"Sale {invoice_num}"
            )
            db.session.add(log)

        # 4. Final Updates
        new_sale.total_amount = total_amount
        new_sale.net_total = total_amount - discount
        new_sale.paid_amount = new_sale.net_total # Assuming full payment for now
        
        # ---------------------------------------------------
        # INTEGRATION: Auto-create Journal Entry (POS)
        # ---------------------------------------------------
        try:
             # Accounts
            revenue_acc = Account.query.filter_by(code='4000').first() # Sales Revenue
            cash_acc = Account.query.filter_by(code='1000').first()    # Cash (Petty/Main)
            
            # For COGS (Cost of Goods Sold) - Advanced
            cogs_acc = Account.query.filter_by(code='5000').first()      # COGS
            inventory_acc = Account.query.filter_by(code='1300').first() # Inventory Asset
            
            if revenue_acc and cash_acc:
                je = JournalEntry(
                    date=datetime.utcnow(),
                    reference=invoice_num,
                    description=f"POS Sale - {customer_name}",
                    user_id=current_user.id
                )
                
                # 1. Revenue Entry
                # Dr Cash (Total Paid)
                je.items.append(JournalItem(account_id=cash_acc.id, debit=new_sale.paid_amount, credit=0))
                
                # Cr Revenue (Net Total)
                je.items.append(JournalItem(account_id=revenue_acc.id, credit=new_sale.net_total, debit=0))
                
                # Cr Discount (if any)? Usually tracked as separate expense or contra-revenue
                # For simplicity, we just booked net revenue above.
                
                # 2. COGS Entry (Perpetual Inventory System)
                # We need to calculate total cost of items sold
                total_cost = 0
                for item in cart_items:
                    batch = Batch.query.get(item['batch_id'])
                    if batch:
                        total_cost += (batch.unit_cost * float(item['quantity']))
                
                if cogs_acc and inventory_acc and total_cost > 0:
                    # Dr COGS
                    je.items.append(JournalItem(account_id=cogs_acc.id, debit=total_cost, credit=0))
                    # Cr Inventory Asset
                    je.items.append(JournalItem(account_id=inventory_acc.id, credit=total_cost, debit=0))
                
                db.session.add(je)
                
        except Exception as e:
            current_app.logger.error(f"POS Accounting Integration Error: {e}")
            # Non-blocking error

        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Sale completed successfully',
            'invoice_number': invoice_num,
            'sale_id': new_sale.id
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"POS checkout error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/list')
@login_required
@permission_required('view_sales')
def list_sales():
    """View list of past sales."""
    sales = Sale.query.order_by(Sale.created_at.desc()).all()
    return render_template('sales/list.html', sales=sales)
