from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Category')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=150)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    barcode = StringField('Barcode / SKU', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    base_unit = StringField('Base Unit (e.g. Tab, Bottle, Box)', default='Unit', validators=[DataRequired()])
    submit = SubmitField('Save Product')

class BatchForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    batch_number = StringField('Batch Number', validators=[DataRequired(), Length(max=100)])
    expiry_date = DateField('Expiry Date', validators=[DataRequired()])
    unit_cost = FloatField('Unit Cost Price', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField('Unit Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = FloatField('Initial Quantity', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Stock Batch')

class ImportInventoryForm(FlaskForm):
    import_file = FileField('Upload Inventory CSV/Excel', validators=[
        FileRequired(),
        FileAllowed(['csv', 'xlsx', 'xls'], 'CSV or Excel files only!')
    ])
    submit = SubmitField('Import Inventory')
