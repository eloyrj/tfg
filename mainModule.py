#!/usr/bin/env python
import threading
import pika, sys, os
from fastapi import FastAPI
import requests
import json 
from api import *
import logging
import logging.handlers

 
class moduloPrincipal:
    def __init__(self):
        """
            Constructor del módulo principal, este va a iniciar todos los parametros necesarios para el funcionamiento del mismo.
        """

        # se inicializan la conexión con rabitmq
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        # Inicialización de los módulos conectados.
        self.modulosConectado = {"modulosDeteccion":[], "modulosActuacion":[]}

        # Configuración de logs
        # Configurar el registro
        self.logger = logging.getLogger('droneSecure')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler('droneSecure.log', maxBytes=1024, backupCount=3)
        # Establecer el formato de los mensajes de registro
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        # Agregar el manejador de registro al objeto Logger
        self.logger.addHandler(handler)

    def main(self):
        # Declaración de cola de conexion para Modulos de detección
        self.channel.queue_declare(queue='detectConnect')
        self.channel.basic_consume(queue='detectConnect', on_message_callback=self.detectModuleConnected, auto_ack=True)
        # Declaración de cola de desconexion para Modulos de detección
        self.channel.queue_declare(queue='detectDisconnect')
        self.channel.basic_consume(queue='detectDisconnect', on_message_callback=self.detectModuleDisconnected, auto_ack=True)

        # Declaración de cola de conexion para Modulos de acción
        self.channel.queue_declare(queue='actionConnect')
        self.channel.basic_consume(queue='actionConnect', on_message_callback=self.actionModuleConnected, auto_ack=True)
        # Declaración de cola de desconexion para Modulos de acción
        self.channel.queue_declare(queue='actionDisconnect')
        self.channel.basic_consume(queue='actionDisconnect', on_message_callback=self.actionModuleDisconnected, auto_ack=True)

        # Declaración de cola los mensajes de detección
        self.channel.queue_declare(queue='camera')
        self.channel.basic_consume(queue='camera', on_message_callback=self.camaraDeteta, auto_ack=True)

        self.logger.info("[*] Modulo principal Iniciado.")
        print(' [*] Modulo principal a la espera de detecciones. Para salir presione CTRL+C')

        # Se comienza a leer la cola.
        self.channel.start_consuming()

    def camaraDeteta(self,ch, method, properties, body):
            """ 
                Función encargada de recibir y manejar las incidencias de los módulos de detección
            """

            for modulos in self.modulosConectado["modulosDeteccion"]:
                if modulos["id"] == body.decode('utf-8'):
                    camara = modulos

                    # Se muestra la información en los logs
                    self.logger.warning(f" [x] Dron detectado por la camara {camara['id']}")
                    print(f" [x] Dron detectado por la camara {camara['id']}")

                    for actuador in self.modulosConectado["modulosActuacion"]:
                        if actuador["id"] == camara['actionModuleId']:

                            # Mandamos peticion de acción al modulo de acción que tiene asociado el modulo de detección
                            self.channel.basic_publish(exchange='', routing_key='Actua'+actuador["id"], body="")
                             

    def detectModuleConnected(self,ch, method, properties, body):
            """ 
                Función para la conexión de nuevos modulos de detección.
            """

            ids = str(body.decode('utf-8')).split("%k%")
            self.modulosConectado["modulosDeteccion"].append({"id":ids[0], "actionModuleId":ids[1]})

            # Se manda la nueva información de los modulos a la api
            api_url = "http://127.0.0.1:8000/set_modulos"
            data = {'modulos':json.dumps(self.modulosConectado)}
            requests.post(api_url ,params=data)
            # Se muestra la información en los logs
            self.logger.info(f" [x] Nuevo modulo de detección Conectado con ID = {ids[0]}")
            print(f" [x] Nuevo modulo de detección Conectado con ID = {ids[0]}")
    
    def detectModuleDisconnected(self,ch, method, properties, body):
            """ 
                Función para la desconexión de modulos de detección.
            """

            for modulos in self.modulosConectado["modulosDeteccion"]:
                if modulos["id"] == str(body.decode('utf-8')):
                    camara = modulos
                    self.modulosConectado["modulosDeteccion"].remove(camara)
                    api_url = "http://127.0.0.1:8000/set_modulos"
                    data = {'modulos':json.dumps(self.modulosConectado)}
                    requests.post(api_url ,params=data)
                    # Se muestra la información en los logs
                    self.logger.info(f" [x]  Modulo de detección con ID = {camara['id']} ha sido desconectado")
                    print(f" [x]  Modulo de detección con ID = {camara['id']} ha sido desconectado")


    def actionModuleConnected(self,ch, method, properties, body):
            """ 
                Función para la conexión de nuevos modulos de acción. 
            """
            
            idasignada = str(body.decode('utf-8'))
            self.modulosConectado["modulosActuacion"].append({"id":idasignada})
            api_url = "http://127.0.0.1:8000/set_modulos"
            data = {'modulos':json.dumps(self.modulosConectado)}
            requests.post(api_url ,params=data)
            # Se muestra la información en los logs
            self.logger.info(f" [x] Nuevo modulo de Acción Conectado ID = {idasignada}")
            print(f" [x] Nuevo modulo de Acción Conectado ID = {idasignada}")
    
    def actionModuleDisconnected(self,ch, method, properties, body):
            """ 
                Función para la desconexión de modulos de acción 
            """

            for modulos in self.modulosConectado["modulosActuacion"]:
                if modulos["id"] == str(body.decode('utf-8')):
                    camara = modulos
                    self.modulosConectado["modulosActuacion"].remove(camara)
                    api_url = "http://127.0.0.1:8000/set_modulos"
                    data = {'modulos':json.dumps(self.modulosConectado)}
                    requests.post(api_url ,params=data)
                    # Se muestra la información en los logs
                    self.logger.info(f" [x]  Modulo de acción con ID = {camara['id']} ha sido desconectado")
                    print(f" [x]  Modulo de acción con ID = {camara['id']} ha sido desconectado")

    def getModulosConectados(self):
         return self.modulosConectado

    def pararModulo(self):
         """
            Función para acciones que se realizan al parar el módulo principal.
         """

         # Se muestra la información en los logs
         self.logger.info("[*] Modulo principal Parado.")


modulo = moduloPrincipal()

if __name__ == '__main__':
    try:
        modulo.main()
    except KeyboardInterrupt:
        modulo.pararModulo()
        print('Modulo parado')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)



