from sqlalchemy.orm import Session
from sqlalchemy import and_
# Ajusta estas rutas a donde tengas realmente tus modelos
from app.models.auditoria_model import Auditoria
from app.models.administrador_model import Administrador
from app.models.usuario_model import Usuario
from app.models.validacion_model import ValidacionUsuario

class AuditoriaService:

    @staticmethod
    def get_historial_auditorias(db: Session):
        resultados = (
            db.query(
                Auditoria,
                Usuario.nombre_completo,
                ValidacionUsuario.estado_validacion,
                ValidacionUsuario.motivo_rechazo
            )
            .join(Administrador, Auditoria.id_admin == Administrador.id_administrador)
            .join(Usuario, Administrador.id_usuario == Usuario.id_usuario)
            .outerjoin(
                ValidacionUsuario,
                and_(
                    Auditoria.tabla_afectada == 'validacion_usuario',
                    Auditoria.id_objetivo == ValidacionUsuario.id_validacion # O el nombre de la PK en esa tabla
                )
            )
            .order_by(Auditoria.fecha.desc())
            .all()
        )

        historial_enriquecido = []
        for auditoria, nombre_admin, estado_val, motivo_rech in resultados:
            registro = {
                "id_auditoria": auditoria.id_auditoria,
                "id_admin": auditoria.id_admin,
                "nombre_admin": nombre_admin,  # <-- Dato del Usuario
                "accion": auditoria.accion,
                "tabla_afectada": auditoria.tabla_afectada,
                "id_objetivo": auditoria.id_objetivo,
                "detalle": auditoria.detalle,
                "fecha": auditoria.fecha,
                "ip_origen": auditoria.ip_origen,
                "estado_validacion": estado_val, # <-- Dato de Validación (Nulo si es otra tabla)
                "motivo_rechazo": motivo_rech    # <-- Dato de Validación (Nulo si es otra tabla)
            }
            historial_enriquecido.append(registro)

        return historial_enriquecido