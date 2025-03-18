from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime , date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import and_
from forms import Turno
import random
import calendar
import colorsys



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

# Usuarios
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Turnos Médicos
class Turno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    fecha_trabajo = db.Column(db.Date, nullable=False)
    horas_trabajadas = db.Column(db.Integer, nullable=False)
    turno = db.Column(db.String(10), nullable=False)
    
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

@app.route('/nuevo_doctor', methods=['GET', 'POST'])
def nuevo_doctor():
    if request.method == 'POST':
        nombre_doctor = request.form.get('nombre')
        if nombre_doctor:
            try:
                nuevo_doctor = Doctor(name=nombre_doctor)
                db.session.add(nuevo_doctor)
                db.session.commit()
                flash("✅ Doctor agregado con éxito.", "success")
            except:
                flash("❌ Error: El doctor ya está registrado o hubo un problema.", "danger")
        else:
            flash("⚠️ El nombre del doctor es obligatorio.", "warning")
    
    # 🔹 Obtener todos los doctores de la base de datos
    doctores = Doctor.query.all()
    
    # 🔹 Enviar la lista de doctores a la plantilla
    return render_template('nuevo_doctor.html', doctores=doctores)

# Ruta para eliminar un doctor
@app.route('/eliminar_doctor/<int:id>', methods=['POST'])
def eliminar_doctor(id):
    doctor = Doctor.query.get(id)
    if doctor:
        try:
            db.session.delete(doctor)
            db.session.commit()
            flash("✅ Doctor eliminado con éxito.", "success")
        except:
            flash("❌ Error al eliminar el doctor.", "danger")
    else:
        flash("⚠️ Doctor no encontrado.", "warning")
    return redirect(url_for('nuevo_doctor'))

# Ruta para editar un doctor
@app.route('/editar_doctor/<int:id>', methods=['POST'])
def editar_doctor(id):
    nuevo_nombre = request.form.get('nuevo_nombre')
    doctor = Doctor.query.get(id)
    if doctor and nuevo_nombre:
        try:
            doctor.name = nuevo_nombre
            db.session.commit()
            flash("✅ Doctor actualizado con éxito.", "success")
        except:
            flash("❌ Error al actualizar el doctor.", "danger")
    else:
        flash("⚠️ El nombre no puede estar vacío.", "warning")
    return redirect(url_for('nuevo_doctor'))


# Opciones de áreas médicas
opciones = [
    "Observ - Medico 1 (JG)", "Observ - Medico 2", "Shock T", "Observ - Medico 3",
    "TÓPICO 1", "TÓPICO 2", "TOPICO 3", "TOPICO 4", "TRIAJE 1", "TRIAJE 2"
]

@app.route('/')
def index():
    if 'user_id' in session:
        turnos = Turno.query.all()  
        doctores = Doctor.query.all()
        return render_template(
            'index.html', 
            username=session['username'], 
            turnos=turnos, 
            opciones=opciones, 
            datetime=datetime,
            doctores=doctores
        )
    else:
        return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('El usuario ya existe. Elija otro.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registro exitoso. Ahora puede iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Sesión cerrada.', 'success')
    return redirect(url_for('login'))

@app.route("/turnos", methods=["GET", "POST"])
def turnos():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        area = request.form.get("area")
        fecha_trabajo = request.form.get("fecha_trabajo")
        horas_trabajadas = request.form.get("horas_trabajadas")
        turno = request.form.get("turno")
        

        if not nombre or not area or not fecha_trabajo or not horas_trabajadas or not turno:
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for("turnos"))

        nuevo_turno = Turno(
            doctor=nombre, area=area, fecha_trabajo=datetime.strptime(fecha_trabajo, "%Y-%m-%d").date(),
            horas_trabajadas=int(horas_trabajadas), turno=turno
        )
        db.session.add(nuevo_turno)
        db.session.commit()
        flash("Turno agregado con éxito.", "success")
        return redirect(url_for("turnos"))

    turnos = Turno.query.all()
    doctores = Doctor.query.all()
    return render_template("index.html", opciones=opciones, turnos=turnos, datetime=datetime, doctores=doctores)


@app.route("/calendario")
def calendario():
    turnos = Turno.query.all()
    return render_template("calendario.html", turnos=turnos)

@app.route("/borrar/<int:id>")
def borrar(id):
    turno = Turno.query.get(id)
    if turno:
        db.session.delete(turno)
        db.session.commit()
        flash("Turno eliminado.", "success")
    return redirect(url_for("turnos"))

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    turno = Turno.query.get(id)
    if not turno:
        return redirect(url_for("turnos"))

    if request.method == "POST":
        turno.doctor = request.form.get("nombre")
        turno.area = request.form.get("area")
        turno.fecha_trabajo = datetime.strptime(request.form.get("fecha_trabajo"), "%Y-%m-%d").date()
        turno.horas_trabajadas = int(request.form.get("horas_trabajadas", 0))
        turno.turno = request.form.get("turno")

        db.session.commit()
        flash("Turno actualizado.", "success")
        return redirect(url_for("turnos"))

    return render_template("editar.html", turno=turno, opciones=opciones)


@app.route('/editar_turno/<int:turno_id>', methods=['GET', 'POST'])
def editar_turno(turno_id):
    turno = Turno.query.get(turno_id)
    if not turno:
        flash("Turno no encontrado.", "danger")
        return redirect(url_for("reporte_abril"))

    if request.method == 'POST':
        turno.doctor = request.form.get("nombre")
        turno.area = request.form.get("area")
        turno.fecha_trabajo = datetime.strptime(request.form.get("fecha_trabajo"), "%Y-%m-%d").date()
        turno.horas_trabajadas = int(request.form.get("horas_trabajadas", 0))
        turno.turno = request.form.get("turno")

        db.session.commit()
        flash("Turno actualizado correctamente.", "success")
        return redirect(url_for("reporte_abril"))

    return render_template("editar.html", turno=turno, opciones=opciones)


@app.route('/borrar_turno/<int:turno_id>', methods=['POST'])
def borrar_turno(turno_id):
    turno = Turno.query.get(turno_id)
    if turno:
        db.session.delete(turno)
        db.session.commit()
        flash("Turno eliminado correctamente.", "success")
    else:
        flash("Turno no encontrado.", "danger")
    
    return redirect(url_for("reporte_abril"))


@app.route("/calendario/<int:mes>")
def calendario_mes(mes):
    year = datetime.now().year
    nombre_mes = calendar.month_name[mes] 
    primer_dia_semana, ultimo_dia = calendar.monthrange(year, mes)

    
    if mes < 1 or mes > 12:
        flash("Mes inválido.", "danger")
        return redirect(url_for("index"))

    
    meses_nombres = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    nombre_mes = meses_nombres[mes - 1]
    dias_del_mes = calendar.monthrange(year, mes)[1]
    primer_dia_semana = calendar.monthrange(year, mes)[0]
    inicio_mes = date(year, mes, 1)
    fin_mes = date(year, mes, dias_del_mes)
    turnos = Turno.query.filter(
        Turno.fecha_trabajo >= inicio_mes,
        Turno.fecha_trabajo <= fin_mes
    ).all()
    doctores_unicos = list(set(turno.doctor for turno in turnos))
    def generar_colores_unicos(n):
        """Genera n colores bien diferenciados en formato HEX"""
        colores = []
        for i in range(n):
            h = i / n  
            s = 0.7  
            l = 0.5  
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            color_hex = f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"
            colores.append(color_hex)
        return colores

    colores_generados = generar_colores_unicos(len(doctores_unicos))
    colores_doctores = {doctor: colores_generados[i] for i, doctor in enumerate(doctores_unicos)}

    return render_template(
        'calendario.html', 
        turnos=turnos, 
        nombre_mes=nombre_mes, 
        year=year, 
        dias_del_mes=dias_del_mes,
        primer_dia_semana=primer_dia_semana,
        colores_doctores=colores_doctores,
        datetime=datetime,
        ultimo_dia=ultimo_dia 
    )


@app.route('/reporte', methods=['GET'])
def reporte_mes():
    mes = request.args.get('mes', type=int) 

    if not mes or mes < 1 or mes > 12:
        flash("Mes inválido", "danger")
        return redirect(url_for('index')) 
    
    año_actual = datetime.now().year
    primer_dia = date(año_actual, mes, 1)
    
    if mes == 12:
        ultimo_dia = date(año_actual, 12, 31)  
    else:
        ultimo_dia = date(año_actual, mes + 1, 1) - timedelta(days=1)  
    
    turnos = Turno.query.filter(
        Turno.fecha_trabajo >= primer_dia,
        Turno.fecha_trabajo <= ultimo_dia
    ).all()

    templates_por_mes = {
        1: "reporte_enero.html",
        2: "reporte_febrero.html",
        3: "reporte_marzo.html",
        4: "reporte_abril.html",
        5: "reporte_mayo.html",
        6: "reporte_junio.html",
        7: "reporte_julio.html",
        8: "reporte_agosto.html",
        9: "reporte_septiembre.html",
        10: "reporte_octubre.html",
        11: "reporte_noviembre.html",
        12: "reporte_diciembre.html",
    }

    mes_nombre = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ][mes-1]

    return render_template(
        templates_por_mes[mes],
        turnos=turnos,
        mes=mes,
        mes_nombre=mes_nombre,
        fecha_actual=datetime.now().strftime('%d/%m/%Y')
    )

   
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


