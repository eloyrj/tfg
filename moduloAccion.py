#!/usr/bin/env python
import pika, sys, os
from fastapi import FastAPI
import requests
import json 

 
class moduloAccion:
    def __init__(self,id):
        """ Constructor del módulo de acción, este va a iniciar todos los parametros necesarios para el funcionamiento del mismo.

        Args:
            id (str): Id asociada al módulo.
        """
        
        # Se fija la Id del Módulo.
        self.id=id
        
        # se inicializan la conexión con rabitmq
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        
        
        # conexión con el Módulo principal
        self.channel.basic_publish(exchange='',
                        routing_key='actionConnect',        
                        body=str(self.id))

    def main(self):
        """ Funcion principal del módulo de acción
        """
        
        # Declaración de cola de actuación.
        self.channel.queue_declare(queue='Actua'+self.id)
        self.channel.basic_consume(queue='Actua'+self.id, on_message_callback=self.actua, auto_ack=True)

        print(' [*] Modulo de acctuación a la espera de ordenes. Para salir presione CTRL+C')
        self.channel.start_consuming()

    def actua(self,ch, method, properties, body):
        """Función encargado de actuar en contra de la amenaza detectada.

        Args:
            ch (_type_): _description_
            method (_type_): _description_
            properties (_type_): _description_
            body (_type_): _description_
        """
        
        print(' [*] Modulo de actuación' + self.id +" procede a actuar.")
    
    def desconexion(self):
        """Función encargada de la descoñexion del módulo con el módulo principal.
        """
        
        # Se desconecta el módulo del módulo principal.
        self.channel.basic_publish(exchange='',
                        routing_key='actionDisconnect',
                        body=str(self.id))



modulo = moduloAccion("1")

if __name__ == '__main__':
    try:
        modulo.main()
    except KeyboardInterrupt:
        print('Modulo parado')
        modulo.desconexion()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
