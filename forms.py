from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')




class Turno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    fecha_trabajo = db.Column(db.Date, nullable=False)  # Verifica que exista este campo
    horas_trabajadas = db.Column(db.Integer, nullable=False)
    turno = db.Column(db.String(50), nullable=False)
