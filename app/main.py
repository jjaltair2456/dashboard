from pathlib import Path
from typing import List, Optional
from datetime import date

from fastapi import FastAPI, Depends, Request, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import Base, engine, get_db
from app.models import Venta, Empleado, Rol, Categoria

# Apunta a la carpeta app/ donde residen static y templates
BASE_DIR = Path(__file__).resolve().parent

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise Retail API")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# --- Esquemas Pydantic ---
class RolSchema(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    class Config:
        from_attributes = True

class EmpleadoSchema(BaseModel):
    id: int
    nombre: str
    email: str
    rol: Optional[RolSchema] = None
    class Config:
        from_attributes = True

class VentaSchema(BaseModel):
    id: int
    categoria: str
    monto: float
    fecha: date
    empleado_id: Optional[int] = None
    class Config:
        from_attributes = True

class CategoriaCreate(BaseModel):
    nombre: str

# --- Rutas del Sistema ---
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# --- Categorías ---
@app.get("/api/v1/categorias")
def obtener_categorias(db: Session = Depends(get_db)):
    cats_db = [c.nombre for c in db.query(Categoria).all()]
    cats_ventas = [c[0] for c in db.query(Venta.categoria).distinct().all() if c[0]]
    return sorted(list(set(cats_db + cats_ventas)))

@app.post("/api/v1/categorias", status_code=201)
def crear_categoria(cat: CategoriaCreate, db: Session = Depends(get_db)):
    nombre_limpio = cat.nombre.strip()
    if not nombre_limpio:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")
    
    existe = db.query(Categoria).filter(Categoria.nombre.ilike(nombre_limpio)).first()
    if existe:
        raise HTTPException(status_code=400, detail="La categoría ya existe")
        
    nueva_categoria = Categoria(nombre=nombre_limpio)
    db.add(nueva_categoria)
    db.commit()
    db.refresh(nueva_categoria)
    return {"mensaje": "Categoría creada exitosamente", "nombre": nueva_categoria.nombre}

# --- Resumen y Ventas ---
@app.get("/api/v1/resumen")
def obtener_resumen(
    categoria: Optional[str] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Venta)
    if categoria:
        query = query.filter(Venta.categoria == categoria)
    if fecha_inicio:
        query = query.filter(Venta.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Venta.fecha <= fecha_fin)

    total_ingresos = query.with_entities(func.sum(Venta.monto)).scalar() or 0.0
    total_ventas = query.count()
    ticket_promedio = total_ingresos / total_ventas if total_ventas > 0 else 0.0

    return {
        "total_ingresos": round(total_ingresos, 2),
        "total_ventas": total_ventas,
        "ticket_promedio": round(ticket_promedio, 2)
    }

@app.get("/api/v1/ventas", response_model=List[VentaSchema])
def obtener_ventas(
    categoria: Optional[str] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Venta)
    if categoria:
        query = query.filter(Venta.categoria == categoria)
    if fecha_inicio:
        query = query.filter(Venta.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Venta.fecha <= fecha_fin)

    return query.all()

# --- Roles y Empleados ---
@app.get("/api/v1/roles", response_model=List[RolSchema])
def obtener_roles(db: Session = Depends(get_db)):
    return db.query(Rol).all()

@app.get("/api/v1/empleados", response_model=List[EmpleadoSchema])
def obtener_empleados(db: Session = Depends(get_db)):
    return db.query(Empleado).all()

@app.get("/api/v1/empleados/top")
def obtener_top_empleados(db: Session = Depends(get_db)):
    resultados = db.query(
        Empleado.nombre,
        func.count(Venta.id).label("total_ventas"),
        func.coalesce(func.sum(Venta.monto), 0.0).label("monto_recaudado")
    ).join(Venta, Empleado.id == Venta.empleado_id, isouter=True)\
     .group_by(Empleado.id)\
     .order_by(func.sum(Venta.monto).desc())\
     .all()

    return [
        {
            "empleado": r.nombre,
            "total_ventas": r.total_ventas,
            "monto_recaudado": round(r.monto_recaudado, 2)
        }
        for r in resultados
    ]