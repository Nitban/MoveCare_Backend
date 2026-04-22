from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.reportes_model import Reporte
from app.models.conductor_model import Conductor
from app.models.pasajero_model import Pasajero  # 🔥 Importante: agregamos el modelo Pasajero
from app.models.administrador_model import Administrador
from app.models.notificaciones_model import Notificacion
from app.schemas.reportes import ReporteCreate
from fastapi import HTTPException


class ReporteService:

    @staticmethod
    def registrar_incidencia(db: Session, datos_capturados: ReporteCreate) -> Reporte:
        try:
            id_reportante_real = None

            # 1. Verificamos si el usuario que reporta es un Conductor
            conductor = db.query(Conductor).filter(Conductor.id_usuario == datos_capturados.id_reportante).first()

            if conductor:
                id_reportante_real = conductor.id_conductor
            else:
                # 2. Si no es conductor, verificamos si es un Pasajero
                pasajero = db.query(Pasajero).filter(Pasajero.id_usuario == datos_capturados.id_reportante).first()
                if pasajero:
                    id_reportante_real = pasajero.id_pasajero

            # 3. Si no existe en ninguna de las dos tablas, bloqueamos el proceso
            if not id_reportante_real:
                raise HTTPException(status_code=404,
                                    detail="El usuario no está registrado como conductor ni como pasajero.")

            # 4. Creamos el reporte usando el ID real que encontramos
            nuevo_reporte = Reporte(
                id_reportante=id_reportante_real,
                id_reportado=datos_capturados.id_reportado,
                tipo_reporte=datos_capturados.tipo_reporte,
                descripcion=datos_capturados.descripcion,
                estado="Pendiente",
                id_viaje=datos_capturados.id_viaje
            )

            db.add(nuevo_reporte)
            db.commit()
            db.refresh(nuevo_reporte)
            return nuevo_reporte

        except HTTPException as http_e:
            raise http_e
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error real de DB: {str(e)}")

    @staticmethod
    def actualizar_estado_reporte(db: Session, id_reporte: str, nuevo_estado: str, id_usuario_admin: str,
                                  motivo_rechazo: str = ""):
        try:
            # 1. Buscar admin
            admin = db.query(Administrador).filter(Administrador.id_usuario == id_usuario_admin).first()
            if not admin:
                raise HTTPException(status_code=403, detail="El usuario no es administrador")

            id_admin_real = str(admin.id_administrador)

            # 2. Buscar reporte
            reporte = db.query(Reporte).filter(Reporte.id_reporte == id_reporte).first()
            if not reporte:
                raise HTTPException(status_code=404, detail="El reporte no existe.")

            # 3. Actualizar reporte
            reporte.estado = nuevo_estado
            reporte.id_admin = id_admin_real
            reporte.motivo_rechazo = motivo_rechazo if nuevo_estado == "Rechazado" else None

            # 🔥 4. Encontrar el id_usuario real evaluando si es Conductor o Pasajero
            id_usuario_real = None

            # Buscamos primero en la tabla de conductores
            conductor_reportante = db.query(Conductor).filter(Conductor.id_conductor == reporte.id_reportante).first()
            if conductor_reportante:
                id_usuario_real = str(conductor_reportante.id_usuario)
            else:
                # Si no es conductor, buscamos en la tabla de pasajeros
                pasajero_reportante = db.query(Pasajero).filter(Pasajero.id_pasajero == reporte.id_reportante).first()
                if pasajero_reportante:
                    id_usuario_real = str(pasajero_reportante.id_usuario)

            # 5. Crear la notificación solo si encontramos al dueño real
            if id_usuario_real:
                id_corto = str(reporte.id_reporte).split('-')[0]
                v_titulo = "¡Tu reporte ha sido aprobado!" if nuevo_estado == "Aceptado" else "Actualización sobre tu reporte"
                v_mensaje = f"Tu reporte #{id_corto} ha sido validado." if nuevo_estado == "Aceptado" else f"Tu reporte #{id_corto} fue descartado. Motivo: {motivo_rechazo}"

                nueva_notificacion = Notificacion(
                    id_usuario=id_usuario_real,  # 🔥 Aquí ya va el ID correcto que la base de datos espera
                    titulo=v_titulo,
                    mensaje=v_mensaje,
                    tipo="actualizacion_reporte"
                )
                db.add(nueva_notificacion)
            else:
                print(f"⚠️ Aviso: No se encontró el id_usuario asociado al reportante {reporte.id_reportante}.")

            # 6. Auditoría
            db.execute(text("SET LOCAL app.current_admin = :admin_id"), {"admin_id": id_admin_real})

            db.commit()
            db.refresh(reporte)
            return reporte

        except HTTPException as http_e:
            raise http_e
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

    @staticmethod
    def obtener_reportes_pendientes(db: Session):
        try:
            return db.query(Reporte).filter(Reporte.estado == "Pendiente").all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al consultar BD: {str(e)}")