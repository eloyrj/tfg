import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

channel.basic_publish(exchange='',
                      routing_key='camera',
                      body=str(1))
print(" [x] Sent 'Hello World!'")

connection.close()