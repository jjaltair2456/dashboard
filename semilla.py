import os
import random
from datetime import date, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Empleado, Rol, Venta

# Eliminar la base de datos previa si existe para evitar desajustes de esquema
if os.path.exists("dashboard.db"):
    os.remove("dashboard.db")

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 1. Crear Roles y guardarlos en variables directas
rol_admin = Rol(nombre="Super Admin", descripcion="Acceso total y configuración")
rol_gerente = Rol(nombre="Gerente", descripcion="Supervisión de ventas y personal")
rol_vendedor = Rol(nombre="Vendedor", descripcion="Atención al cliente y caja")

db.add_all([rol_admin, rol_gerente, rol_vendedor])
db.commit()

# 2. Crear Empleados asignando las instancias de Rol directamente
empleados_vendedores = [
    Empleado(nombre="Carlos Mendoza", email="carlos.mendoza@empresa.com", rol=rol_vendedor),
    Empleado(nombre="Ana Rodríguez", email="ana.rodriguez@empresa.com", rol_id=rol_vendedor.id),
    Empleado(nombre="José Gómez", email="jose.gomez@empresa.com", rol=rol_vendedor),
]
gerente = Empleado(nombre="María Pérez", email="maria.perez@empresa.com", rol=rol_gerente)

db.add_all(empleados_vendedores + [gerente])
db.commit()

# 3. Generar Ventas vinculadas a Empleados Vendedores
categorias = ["Herramientas", "Pinturas", "Electricidad", "Plomería", "Construcción"]
hoy = date.today()

for _ in range(60):
    dias_atras = random.randint(0, 30)
    vendedor_asignado = random.choice(empleados_vendedores)
    
    nueva_venta = Venta(
        categoria=random.choice(categorias),
        monto=round(random.uniform(20.00, 600.00), 2),
        fecha=hoy - timedelta(days=dias_atras),
        empleado=vendedor_asignado
    )
    db.add(nueva_venta)

db.commit()
db.close()
print("✅ Base de datos inicializada: Roles, Empleados y 60 Ventas relacionales creadas.")