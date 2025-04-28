from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import and_
from forms import Turno
import random
import calendar
import colorsys
from sqlalchemy import func
import pandas as pd
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from datetime import datetime
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from openpyxl.styles import Alignment, PatternFill, Border, Side
from openpyxl.styles.fills import GradientFill





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
    horas_trabajadas = db.Column(db.Integer, nullable=False, default=6) 
    turno = db.Column(db.String(10), nullable=False)
    tipo_horas = db.Column(db.String(10), nullable=False)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

@app.route('/nuevo_doctor', methods=['GET', 'POST'])
def nuevo_doctor():
    if request.method == 'POST':
        nombre_doctor = request.form.get('nombre')
        if nombre_doctor:
            doctor_existente = Doctor.query.filter_by(name=nombre_doctor).first()
            if doctor_existente:
                flash("❌ Error: El doctor ya está registrado.", "danger")
            else:
                try:
                    nuevo_doctor = Doctor(name=nombre_doctor)
                    db.session.add(nuevo_doctor)
                    db.session.commit()
                    flash("✅ Doctor agregado con éxito.", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"❌ Error: Hubo un problema al registrar el doctor. {str(e)}", "danger")
        else:
            flash("⚠️ El nombre del doctor es obligatorio.", "warning")
    
    doctores = Doctor.query.all()
    return render_template('nuevo_doctor.html', doctores=doctores)

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

opciones = [
    "Observ - Medico 1 (JG)", "Observ - Medico 2", "Shock T", "Observ - Medico 3",
    "TÓPICO 1", "TÓPICO 2", "TÓPICO 3", "TÓPICO 4", "TRIAJE 1", "TRIAJE 2"
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

@app.route('/turnos', methods=['GET', 'POST'])
def turnos():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        area = request.form.get("area")
        fecha_trabajo = request.form.get("fecha_trabajo")
        horas_trabajadas = int(request.form.get("horas_trabajadas"))
        turno = request.form.get("turno")
        
        if not nombre or not area or not fecha_trabajo or not horas_trabajadas or not turno:
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for("turnos"))
        
        fecha = datetime.strptime(fecha_trabajo, "%Y-%m-%d").date()
        inicio_mes = date(fecha.year, fecha.month, 1)
        fin_mes = date(fecha.year, fecha.month, calendar.monthrange(fecha.year, fecha.month)[1])
        
        # Calcular horas normales y extras existentes
        total_horas_normales = db.session.query(func.sum(Turno.horas_trabajadas)).filter(
            and_(
                func.lower(Turno.doctor) == nombre.lower(),
                Turno.fecha_trabajo.between(inicio_mes, fin_mes),
                Turno.tipo_horas == "Normal"
            )
        ).scalar() or 0

        total_horas_extras = db.session.query(func.sum(Turno.horas_trabajadas)).filter(
            and_(
                func.upper(Turno.doctor) == nombre.upper(),
                Turno.fecha_trabajo.between(inicio_mes, fin_mes),
                Turno.tipo_horas == "Extra"
            )
        ).scalar() or 0

        # Verificar límites antes de asignar horas
        if total_horas_normales >= 150 and total_horas_extras >= 100:
            flash(f"El doctor {nombre} ya ha completado sus 150 horas normales y 100 horas extras este mes.", "danger")
            return redirect(url_for("turnos"))
        
        # Determinar cómo asignar las nuevas horas
        horas_restantes_normales = max(0, 150 - total_horas_normales)
        horas_restantes_extras = max(0, 100 - total_horas_extras)
        
        if total_horas_normales < 150:
            # Asignar primero a horas normales
            if total_horas_normales + horas_trabajadas <= 150:
                # Todo como horas normales
                nuevo_turno = Turno(
                    doctor=nombre.lower(), 
                    area=area, 
                    fecha_trabajo=fecha,
                    horas_trabajadas=horas_trabajadas, 
                    turno=turno, 
                    tipo_horas="Normal"
                )
                db.session.add(nuevo_turno)
            else:
                # Parte normal, parte extra
                horas_normales = 150 - total_horas_normales
                horas_extras = horas_trabajadas - horas_normales
                
                # Registrar horas normales
                if horas_normales > 0:
                    db.session.add(Turno(
                        doctor=nombre.lower(), 
                        area=area, 
                        fecha_trabajo=fecha,
                        horas_trabajadas=horas_normales, 
                        turno=turno, 
                        tipo_horas="Normal"
                ))
                
                # Registrar horas extras si hay capacidad
                if horas_extras > 0 and total_horas_extras < 100:
                    horas_extras_posibles = min(horas_extras, 100 - total_horas_extras)
                    db.session.add(Turno(
                        doctor=nombre.upper(), 
                        area=area, 
                        fecha_trabajo=fecha,
                        horas_trabajadas=horas_extras_posibles, 
                        turno=turno, 
                        tipo_horas="Extra"
                    ))
                    
                    if horas_extras > horas_extras_posibles:
                        flash(f"Solo se pudieron asignar {horas_extras_posibles} horas extras de las {horas_extras} solicitadas (límite: 100 horas extras/mes)", "warning")
        else:
            # Solo asignar horas extras si hay capacidad
            if total_horas_extras < 100:
                horas_extras_posibles = min(horas_trabajadas, 100 - total_horas_extras)
                db.session.add(Turno(
                    doctor=nombre.upper(), 
                    area=area, 
                    fecha_trabajo=fecha,
                    horas_trabajadas=horas_extras_posibles, 
                    turno=turno, 
                    tipo_horas="Extra"
                ))
                
                if horas_trabajadas > horas_extras_posibles:
                    flash(f"Solo se pudieron asignar {horas_extras_posibles} horas extras de las {horas_trabajadas} solicitadas (límite: 100 horas extras/mes)", "warning")
            else:
                flash(f"El doctor {nombre} ya ha completado sus 100 horas extras este mes.", "danger")
                return redirect(url_for("turnos"))
        
        try:
            db.session.commit()
            flash("Turno agregado con éxito.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al guardar el turno: {str(e)}", "danger")
        
        return redirect(url_for("turnos"))

    turnos = Turno.query.all()
    doctores = Doctor.query.all()
    return render_template("index.html", turnos=turnos, doctores=doctores, opciones=opciones, datetime=datetime)

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

@app.route('/editar_turno/<int:id>', methods=['GET', 'POST'])
def editar_turno(id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión primero', 'danger')
        return redirect(url_for('login'))

    turno = Turno.query.get(id)
    if not turno:
        flash('Turno no encontrado', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Guardar valores originales para cálculos
            horas_original = turno.horas_trabajadas
            tipo_original = turno.tipo_horas
            
            # Obtener nuevos valores
            nuevo_nombre = request.form.get('nombre')
            nueva_area = request.form.get('area')
            nueva_fecha = datetime.strptime(request.form.get('fecha_trabajo'), '%Y-%m-%d').date()
            nuevas_horas = int(request.form.get('horas_trabajadas', 6))
            nuevo_turno = request.form.get('turno')
            
            # Calcular periodo mensual
            inicio_mes = date(nueva_fecha.year, nueva_fecha.month, 1)
            fin_mes = date(nueva_fecha.year, nueva_fecha.month, 
                         calendar.monthrange(nueva_fecha.year, nueva_fecha.month)[1])
            
            # Calcular horas actuales
            total_horas_normales = db.session.query(func.sum(Turno.horas_trabajadas)).filter(
                and_(
                    func.lower(Turno.doctor) == nuevo_nombre.lower(),
                    Turno.fecha_trabajo.between(inicio_mes, fin_mes),
                    Turno.tipo_horas == "Normal",
                    Turno.id != turno.id  # Excluir el turno actual
                )
            ).scalar() or 0

            total_horas_extras = db.session.query(func.sum(Turno.horas_trabajadas)).filter(
                and_(
                    func.upper(Turno.doctor) == nuevo_nombre.upper(),
                    Turno.fecha_trabajo.between(inicio_mes, fin_mes),
                    Turno.tipo_horas == "Extra",
                    Turno.id != turno.id  # Excluir el turno actual
                )
            ).scalar() or 0

            # Determinar tipo de horas para el turno editado
            if tipo_original == "Normal":
                total_horas_normales += horas_original
            else:
                total_horas_extras += horas_original

            # Verificar límites con las nuevas horas
            if tipo_original == "Normal":
                if (total_horas_normales - horas_original + nuevas_horas) > 150:
                    flash("No se puede asignar más de 150 horas normales por mes", "danger")
                    return redirect(url_for('editar_turno', id=id))
            else:
                if (total_horas_extras - horas_original + nuevas_horas) > 100:
                    flash("No se puede asignar más de 100 horas extras por mes", "danger")
                    return redirect(url_for('editar_turno', id=id))

            # Actualizar datos del turno
            turno.doctor = nuevo_nombre.lower() if tipo_original == "Normal" else nuevo_nombre.upper()
            turno.area = nueva_area
            turno.fecha_trabajo = nueva_fecha
            turno.horas_trabajadas = nuevas_horas
            turno.turno = nuevo_turno
            
            db.session.commit()
            flash('Turno actualizado correctamente', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar turno: {str(e)}', 'danger')
    
    return render_template('editar_turno.html', 
                         turno=turno, 
                         opciones=opciones,
                         datetime=datetime,
                         doctores=Doctor.query.all())

@app.route('/borrar_turno/<int:id>', methods=['POST'])
def borrar_turno(id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión primero', 'danger')
        return redirect(url_for('login'))

    turno = Turno.query.get(id)
    if turno:
        try:
            db.session.delete(turno)
            db.session.commit()
            flash('Turno eliminado correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar turno: {str(e)}', 'danger')
    else:
        flash('Turno no encontrado', 'warning')
    
    return redirect(url_for('index'))

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


 


@app.route('/descargar_excel')
def descargar_excel():
    try:
        # Obtener parámetros de mes y año
        mes = request.args.get('mes', default=datetime.now().month, type=int)
        año = request.args.get('año', default=datetime.now().year, type=int)
        
        # Validar el mes
        if not 1 <= mes <= 12:
            flash("Mes inválido", "danger")
            return redirect(url_for('index'))
        
        MESES = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        nombre_mes = MESES[mes - 1]
        
        # Obtener los turnos del mes seleccionado
        primer_dia = date(año, mes, 1)
        ultimo_dia = date(año, mes + 1, 1) - timedelta(days=1) if mes < 12 else date(año, 12, 31)
        
        # Consulta a base de datos
        turnos = Turno.query.filter(
            Turno.fecha_trabajo >= primer_dia,
            Turno.fecha_trabajo <= ultimo_dia
        ).order_by(Turno.fecha_trabajo, Turno.area).all()
        
        if not turnos:
            flash(f"No hay turnos registrados para {nombre_mes} {año}", "warning")
            return redirect(url_for('index'))
        
        # Verificar límite de 250 horas por doctor
        doctores_con_exceso = []
        horas_por_doctor = {}

        for turno in turnos:
            doctor = turno.doctor
            if doctor not in horas_por_doctor:
                horas_por_doctor[doctor] = 0
            horas_por_doctor[doctor] += turno.horas_trabajadas

            # Mostrar alerta inmediata cuando se superan las 250 horas
            if horas_por_doctor[doctor] > 250 and doctor not in doctores_con_exceso:
                doctores_con_exceso.append(doctor)
                flash(f"¡ATENCIÓN! El doctor {doctor} ha superado las 250 horas permitidas (total: {horas_por_doctor[doctor]} horas)", "danger")

        # Crear libro de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Turnos {nombre_mes}"
        
        # ========= ESTILOS =========
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        pink_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        area_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        center = Alignment(horizontal="center", vertical="center")
        wrap_text = Alignment(wrap_text=True, horizontal="center", vertical="center")
        yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        light_blue_fill = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
        total_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")
        
        # Estilo de borde para celdas principales
        border_style = Border(
            left=Side(style='medium', color='000000'),
            right=Side(style='medium', color='000000'),
            top=Side(style='medium', color='000000'),
            bottom=Side(style='medium', color='000000')
        )
        
        # Borde para todas las celdas internas
        cell_border = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
        
        # Paleta de colores más vibrantes para doctores
        COLORES_DOCTORES = [
            "FF9999", "CC99FF", "99FF99", "99CCFF", "FFCC99",  # Stronger Red, Purple, Green, Blue, Orange
            "FFFF99", "99FFFF", "CCFFCC", "FFCCFF", "FFCC66",  # Yellow, Cyan, Mint, Pink, Peach
            "FF9966", "66CCCC", "CCCCCC", "FF99CC", "CCCC99",  # Coral, Teal, Gray, Rose, Olive
            "FFCC00", "99CC99", "FFCCCC", "FFFFCC", "CCFFFF",  # Amber, Sage, Soft Pink, Pale Yellow, Sky Blue
            "CC99CC", "99FFCC", "CCCCFF", "FF99FF", "99CCCC",  # Lavender, Mint Green, Periwinkle, Magenta, Aqua
            "FF6666", "66FF99", "6699FF", "FFCC99", "99FF66",  # Bright Red, Lime, Sky, Peach, Chartreuse
            "CC6699", "66CC99", "9999FF", "FF99CC", "66CCCC"   # Plum, Seafoam, Indigo, Blush, Turquoise
        ]
        
        # Normalización de nombres para asignación de colores
        doctores_unicos = list({turno.doctor.lower() for turno in turnos})
        doctor_colores = {doctor: COLORES_DOCTORES[i % len(COLORES_DOCTORES)] 
                         for i, doctor in enumerate(doctores_unicos)}
        
        # ========= FORMATO PRINCIPAL =========
        # Cabecera principal (mes)
        ws.merge_cells('A1:B1')
        ws['A1'] = nombre_mes
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].alignment = center
        ws['A1'].fill = header_fill 
        ws['A1'].border = border_style
        ws['B1'].border = border_style
        
        # Días del mes
        dias_mes = list(range(1, ultimo_dia.day + 1))
        DIAS_SEMANA = ["L", "M", "M", "J", "V", "S", "D"]

        # Calcular el ancho máximo necesario para las columnas de días
        max_width_per_column = {col: 15 for col in range(2, len(dias_mes) + 2)}  # Ancho base de 15

        # Reasignar áreas para turnos de NOCHE antes de agrupar
        for turno in turnos:
            turno_tipo = (turno.turno or "MAÑANA").upper()
            if turno_tipo not in ["MAÑANA", "TARDE", "NOCHE"]:
                turno_tipo = "MAÑANA"
            if turno_tipo == "NOCHE":
                if turno.area not in ["Jefe G.", "G.N.", "Triaje"]:
                    print(f"Reassigning area for doctor {turno.doctor} in NOCHE shift from {turno.area} to G.N.")
                    turno.area = "G.N."

        # Recorrer los turnos para determinar el ancho necesario según los nombres de doctores
        doctores_por_dia_area = {}
        for turno in turnos:
            turno_tipo = (turno.turno or "MAÑANA").upper()
            if turno_tipo not in ["MAÑANA", "TARDE", "NOCHE"]:
                turno_tipo = "MAÑANA"
            
            key = (turno_tipo, turno.area, turno.fecha_trabajo.day)
            if key not in doctores_por_dia_area:
                doctores_por_dia_area[key] = []
            doctores_por_dia_area[key].append(turno)

        for key, turnos_dia in doctores_por_dia_area.items():
            turno_tipo, area, dia = key
            dia_col = dia + 1
            doctores_info = [{"nombre": turno.doctor} for turno in turnos_dia]
            max_name_length = max(len(doc["nombre"]) for doc in doctores_info) if doctores_info else 10
            column_width = max_name_length * 1.2
            max_width_per_column[dia_col] = max(max_width_per_column[dia_col], column_width)

        # ========= ORGANIZACIÓN POR TURNOS =========
        AREAS_MEDICAS = [
            "Observ - Medico 1 (JG)", 
            "Observ - Medico 2", 
            "Shock T", 
            "Observ - Medico 3",
            "TÓPICO 1", 
            "TÓPICO 2", 
            "TÓPICO 3", 
            "TÓPICO 4", 
            "TRIAJE 1", 
            "TRIAJE 2"
        ]
        
        AREAS_NOCHE = [
            "Jefe G.", 
            "G.N.", 
            "Triaje"
        ]

        turnos_config = [
            ("MAÑANA", pink_fill, AREAS_MEDICAS),
            ("TARDE", pink_fill, AREAS_MEDICAS),
            ("NOCHE", pink_fill, AREAS_NOCHE)
        ]

        max_area_length = max(len(area) for area in AREAS_MEDICAS + AREAS_NOCHE) if AREAS_MEDICAS or AREAS_NOCHE else 15
        ws.column_dimensions['A'].width = max(max_area_length * 1.2, 20)

        current_row = 3
        areas_rows = {}  # Initialize the dictionary to store area-to-row mappings

        for turno_idx, (turno_nombre, fill_color, areas_turno) in enumerate(turnos_config):
            start_row = current_row
            end_row = current_row + 1
            
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row+1, end_column=1)
            ws.cell(row=current_row, column=1, value=turno_nombre)
            ws.cell(row=current_row, column=1).font = Font(bold=True, size=12)
            ws.cell(row=current_row, column=1).alignment = center
            ws.cell(row=current_row, column=1).fill = fill_color
            ws.cell(row=current_row, column=1).border = border_style
            ws.row_dimensions[current_row].height = 30
            ws.row_dimensions[current_row+1].height = 30
            
            for r in range(current_row, current_row+2):
                ws.cell(row=r, column=1).border = border_style
            
            for col, dia_num in enumerate(dias_mes, start=2):
                dia_letra = DIAS_SEMANA[date(año, mes, dia_num).weekday()]
                celda_dia = ws.cell(row=current_row, column=col, value=dia_letra)
                celda_dia.fill = fill_color
                celda_dia.alignment = center
                celda_dia.border = cell_border
                
                celda_num = ws.cell(row=current_row+1, column=col, value=dia_num)
                celda_num.fill = fill_color
                celda_num.alignment = center
                celda_num.border = cell_border

                ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = max_width_per_column[col]
            
            current_row += 2
            
            for area in areas_turno:
                celda = ws.cell(row=current_row, column=1, value=area)
                celda.alignment = wrap_text
                celda.fill = area_fill
                celda.border = border_style
                ws.row_dimensions[current_row].height = 60
                
                # Map the area to the current row
                areas_rows[(turno_nombre, area)] = current_row
                print(f"Mapping {turno_nombre} - {area} to row {current_row}")
                
                for c in range(1, len(dias_mes)+2):
                    ws.cell(row=current_row, column=c).border = cell_border
                
                current_row += 1
            
            end_row = current_row - 1
            
            for r in range(start_row, end_row + 1):
                ws.cell(row=r, column=1).border = border_style
                ws.cell(row=r, column=len(dias_mes)+1).border = border_style
            
            for c in range(1, len(dias_mes)+2):
                ws.cell(row=start_row, column=c).border = border_style
                ws.cell(row=end_row, column=c).border = border_style
            
            # Espacio entre turnos: 3 filas normales, 4 filas antes de NOCHE
            current_row += 4 if turno_nombre == "TARDE" else 3
        
        # ========= PROCESAR TURNOS =========
        turnos_por_tipo = {
            "MAÑANA": [],
            "TARDE": [],
            "NOCHE": []
        }
        
        for turno in turnos:
            turno_tipo = (turno.turno or "MAÑANA").upper()
            if turno_tipo not in turnos_por_tipo:
                turno_tipo = "MAÑANA"
            turnos_por_tipo[turno_tipo].append(turno)
        
        for key, turnos_dia in doctores_por_dia_area.items():
            turno_tipo, area, dia = key
            area_row = areas_rows.get((turno_tipo, area))
            
            if not area_row:
                print(f"Warning: No row found for {turno_tipo} - {area} on day {dia}. Skipping.")
                continue
                
            dia_col = dia + 1
            
            doctores_info = []
            for turno in turnos_dia:
                color_key = turno.doctor.lower()
                color = doctor_colores.get(color_key, "FFFFFF")
                if turno.tipo_horas == "Extra":
                    color = green_fill.start_color
                
                doctores_info.append({
                    "nombre": turno.doctor,
                    "color": color,
                    "tipo": turno.tipo_horas
                })
            
            doctores_info.sort(key=lambda x: (x["tipo"] != "Normal", x["nombre"]))
            
            texto_doctores = "\n".join(doc["nombre"] for doc in doctores_info)
            
            celda = ws.cell(row=area_row, column=dia_col, value=texto_doctores)
            celda.alignment = Alignment(
                wrap_text=True, 
                horizontal="center", 
                vertical="center",
                shrink_to_fit=False
            )
            celda.border = cell_border
            celda.font = Font(color="000000", size=12, bold=True)

            num_doctores = len(doctores_info)
            max_name_length = max(len(doc["nombre"]) for doc in doctores_info) if doctores_info else 10
            altura_base = 20 * num_doctores
            altura_extra = (max_name_length // 20) * 10
            altura_fila = max(altura_base + altura_extra, 60)
            ws.row_dimensions[area_row].height = altura_fila

            if num_doctores > 1:
                colores = [doctor["color"] for doctor in doctores_info]
                fill = GradientFill(
                    stop=colores,
                    type="linear",
                    degree=90
                )
                celda.fill = fill
            else:
                color = doctores_info[0]["color"]
                celda.fill = PatternFill(
                    start_color=color,
                    end_color=color,
                    fill_type="solid"
                )

        # ========= HOJA DETALLE =========
        ws_detalle = wb.create_sheet(title="Detalle Completo")
        
        headers = ["Doctor", "Área", "Fecha", "Horas Trabajadas", "Turno", "Tipo Horas"]
        for col, header in enumerate(headers, 1):
            celda = ws_detalle.cell(row=1, column=col, value=header)
            celda.font = header_font
            celda.fill = header_fill
            celda.alignment = center
            celda.border = border_style
        
        for row, turno in enumerate(turnos, 2):
            color_key = turno.doctor.lower()
            color_doctor = doctor_colores.get(color_key, "FFFFFF")
            celda_doctor = ws_detalle.cell(row=row, column=1, value=turno.doctor)
            celda_doctor.fill = PatternFill(
                start_color=color_doctor if turno.tipo_horas == "Normal" else green_fill.start_color,
                end_color=color_doctor if turno.tipo_horas == "Normal" else green_fill.end_color,
                fill_type="solid"
            )
            celda_doctor.font = Font(color="000000", size=12, bold=True)
            celda_doctor.border = cell_border

            ws_detalle.cell(row=row, column=2, value=turno.area).border = cell_border
            ws_detalle.cell(row=row, column=3, value=turno.fecha_trabajo).number_format = 'DD/MM/YYYY'
            ws_detalle.cell(row=row, column=3).border = cell_border
            ws_detalle.cell(row=row, column=4, value=turno.horas_trabajadas).border = cell_border
            ws_detalle.cell(row=row, column=5, value=turno.turno or "MAÑANA").border = cell_border
            ws_detalle.cell(row=row, column=6, value=turno.tipo_horas).border = cell_border
        
        max_doctor_length = max(len(turno.doctor) for turno in turnos) if turnos else 20
        doctor_column_width = max(max_doctor_length * 1.5, 40)

        ws_detalle.column_dimensions['A'].width = doctor_column_width
        ws_detalle.column_dimensions['B'].width = 25
        ws_detalle.column_dimensions['C'].width = 12
        ws_detalle.column_dimensions['D'].width = 8
        ws_detalle.column_dimensions['E'].width = 10
        ws_detalle.column_dimensions['F'].width = 12
        
        for row in range(2, len(turnos) + 2):
            ws_detalle.row_dimensions[row].height = 30

        # ========= CUADRO DE RESUMEN =========
        current_row += 5

        doctores_normalizados = {turno.doctor.lower(): turno.doctor for turno in turnos}
        doctores_min = sorted(doctores_normalizados.keys())
        areas = sorted(list({turno.area for turno in turnos}))

        max_doctor_length = max(len(doctores_normalizados.get(doctor, doctor)) for doctor in doctores_min) if doctores_min else 20
        ws.column_dimensions['A'].width = max(max_doctor_length * 1.5, 40)

        resumen_normal = {doctor: {area: 0 for area in areas} for doctor in doctores_min}
        resumen_extra = {doctor: {area: 0 for area in areas} for doctor in doctores_min}

        for turno in turnos:
            doctor_key = turno.doctor.lower()
            if turno.tipo_horas == "Normal":
                resumen_normal[doctor_key][turno.area] += turno.horas_trabajadas
            else:
                resumen_extra[doctor_key][turno.area] += turno.horas_trabajadas

        for doctor in doctores_min:
            total_normal = sum(resumen_normal[doctor].values())
            if total_normal > 150:
                factor = 150 / total_normal
                for area in resumen_normal[doctor]:
                    resumen_normal[doctor][area] = int(resumen_normal[doctor][area] * factor)
            
            total_extra = sum(resumen_extra[doctor].values())
            if total_extra > 100:
                factor = 100 / total_extra
                for area in resumen_extra[doctor]:
                    resumen_extra[doctor][area] = int(resumen_extra[doctor][area] * factor)

        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(areas)+2)
        celda_titulo = ws.cell(row=current_row, column=1, value="HORAS NORMALES POR DOCTOR Y ÁREA ")
        celda_titulo.font = Font(bold=True, size=12)
        celda_titulo.fill = yellow_fill
        celda_titulo.alignment = center
        celda_titulo.border = border_style
        current_row += 1

        ws.cell(row=current_row, column=1, value="DOCTOR").font = Font(bold=True)
        ws.cell(row=current_row, column=1).border = border_style
        ws.cell(row=current_row, column=1).alignment = center
        for col, area in enumerate(areas, start=2):
            ws.cell(row=current_row, column=col, value=area).font = Font(bold=True)
            ws.cell(row=current_row, column=col).fill = area_fill
            ws.cell(row=current_row, column=col).border = border_style
        
        ws.cell(row=current_row, column=len(areas)+2, value="Total").font = Font(bold=True)
        ws.cell(row=current_row, column=len(areas)+2).fill = total_fill
        ws.cell(row=current_row, column=len(areas)+2).alignment = center
        ws.cell(row=current_row, column=len(areas)+2).border = border_style
        current_row += 1

        for doctor in doctores_min:
            total_doctor = 0
            nombre_mostrar = doctores_normalizados.get(doctor, doctor)
            celda_doctor = ws.cell(row=current_row, column=1, value=nombre_mostrar)
            celda_doctor.font = Font(color="000000", size=12, bold=True)
            celda_doctor.border = border_style
            
            for col, area in enumerate(areas, start=2):
                horas = resumen_normal[doctor][area]
                total_doctor += horas
                celda = ws.cell(row=current_row, column=col, value=horas if horas > 0 else "")
                celda.alignment = center
                celda.border = cell_border
                
                if horas > 0:
                    celda.fill = light_blue_fill
            
            total_doctor = min(total_doctor, 150)
            celda_total = ws.cell(row=current_row, column=len(areas)+2, value=total_doctor)
            celda_total.alignment = center
            celda_total.fill = total_fill
            celda_total.border = border_style
            celda_total.font = Font(bold=True)
            
            ws.row_dimensions[current_row].height = 30
            current_row += 1

        for c in range(1, len(areas)+3):
            ws.cell(row=current_row - len(doctores_min) - 1, column=c).border = border_style
            ws.cell(row=current_row - 1, column=c).border = border_style

        for r in range(current_row - len(doctores_min) - 1, current_row):
            ws.cell(row=r, column=1).border = border_style
            ws.cell(row=r, column=len(areas)+2).border = border_style

        current_row += 2

        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(areas)+2)
        celda_titulo = ws.cell(row=current_row, column=1, value="HORAS EXTRA POR DOCTOR Y ÁREA ")
        celda_titulo.font = Font(bold=True, size=12)
        celda_titulo.fill = PatternFill(start_color="FF9999", end_color="FF9999", fill_type="solid")
        celda_titulo.alignment = center
        celda_titulo.border = border_style
        current_row += 1

        ws.cell(row=current_row, column=1, value="DOCTOR").font = Font(bold=True)
        ws.cell(row=current_row, column=1).border = border_style
        ws.cell(row=current_row, column=1).alignment = center
        for col, area in enumerate(areas, start=2):
            ws.cell(row=current_row, column=col, value=area).font = Font(bold=True)
            ws.cell(row=current_row, column=col).fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
            ws.cell(row=current_row, column=col).border = border_style
        
        ws.cell(row=current_row, column=len(areas)+2, value="Total").font = Font(bold=True)
        ws.cell(row=current_row, column=len(areas)+2).fill = total_fill
        ws.cell(row=current_row, column=len(areas)+2).alignment = center
        ws.cell(row=current_row, column=len(areas)+2).border = border_style
        current_row += 1

        for doctor in doctores_min:
            total_doctor = 0
            nombre_mostrar = doctores_normalizados.get(doctor, doctor).upper()
            celda_doctor = ws.cell(row=current_row, column=1, value=nombre_mostrar)
            celda_doctor.font = Font(color="000000", size=12, bold=True)
            celda_doctor.border = border_style
            
            for col, area in enumerate(areas, start=2):
                horas = resumen_extra[doctor][area]
                total_doctor += horas
                celda = ws.cell(row=current_row, column=col, value=horas if horas > 0 else "")
                celda.alignment = center
                celda.border = cell_border
                
                if horas > 0:
                    celda.fill = PatternFill(start_color="FFDDDD", end_color="FFDDDD", fill_type="solid")
            
            total_doctor = min(total_doctor, 100)
            celda_total = ws.cell(row=current_row, column=len(areas)+2, value=total_doctor)
            celda_total.alignment = center
            celda_total.fill = total_fill
            celda_total.border = border_style
            celda_total.font = Font(bold=True)
            
            ws.row_dimensions[current_row].height = 30
            current_row += 1

        for c in range(1, len(areas)+3):
            ws.cell(row=current_row - len(doctores_min) - 1, column=c).border = border_style
            ws.cell(row=current_row - 1, column=c).border = border_style

        for r in range(current_row - len(doctores_min) - 1, current_row):
            ws.cell(row=r, column=1).border = border_style
            ws.cell(row=r, column=len(areas)+2).border = border_style

        if doctores_con_exceso:
            current_row += 3
            
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(dias_mes)+1)
            celda_advertencia = ws.cell(row=current_row, column=1, 
                                      value=f"ADVERTENCIA: Los siguientes doctores han excedido 250 horas: {', '.join(doctores_con_exceso)}")
            celda_advertencia.font = Font(bold=True, color="FF0000")
            celda_advertencia.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
            celda_advertencia.alignment = center

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        nombre_archivo = f"Turnos_{nombre_mes}_{año}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        flash(f"Error al generar el reporte: {str(e)}", "danger")
        return redirect(url_for('index'))










if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)