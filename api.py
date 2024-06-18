from fastapi import FastAPI
from pydantic import BaseModel

app =FastAPI()

# Inicialización de los módulos conectados.
modulosConectado = {"modulosDeteccion":[], "modulosActuacion":[]}

@app.get("/get_modulos")
async def getModulos():
    """Función encargada de devolver los módulos conectados.

    Returns:
        json: Módulos conectados al módulo principal.
    """
    return {"modulos": modulosConectado}

@app.post("/set_modulos")
async def setModulos(modulos):
    """Función encargada de actualizar los Modulos conectados al módulo principal.

    Args:
        modulos (json): módulos conectados al modulo principal.
    """

    global modulosConectado
    modulosConectado = modulos