import firebase_admin
from firebase_admin import messaging, credentials
from google.cloud.storage import notification




def sendMessage(token : str):
    # This registration token comes from the client FCM SDKs.
    registration_token = token

    # See documentation on defining a message payload.
    message = messaging.Message(
        data={
            'score': '850',
            'time': '2:45',
        },
        token=registration_token,
    )

    # Send a message to the device corresponding to the provided
    # registration token.
    response = messaging.send(message)
    # Response is a message ID string.
    print('Successfully sent message:', response)
    return 'Successfully sent message:', response
