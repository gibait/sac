import argparse
from google.cloud import pubsub_v1
from uuid import uuid1

# CHANGE THESE
ARGUMENT = []
PROJECT_ID = ''

def callback(message):
    print(message.data)
    message.ack()

parser = argparse.ArgumentParser()
parser.add_argument(ARGUMENT, type=str)
args = parser.parse_args()

topic_name = 'projects/{project_id}/topics/{topic}'.format(
    project_id=PROJECT_ID,
    topic=args,  
)

subscription_name = 'projects/{project_id}/subscriptions/{sub}'.format(
    project_id=PROJECT_ID,
    sub=f'{args}-{uuid1()}',
)

with pubsub_v1.SubscriberClient() as subscriber:
    subscriber.create_subscription(
        name=subscription_name,
        topic=topic_name
    )
    print(f"listening on {subscription_name}")
    fut = subscriber.subscribe(subscription_name, callback)
    try:
        fut.result()
    except KeyboardInterrupt:
        fut.cancel()