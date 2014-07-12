import base64
import time
import random
import os

class InvalidToken(BaseException): pass

def serializeXSRFToken(currentTime, entityId, userId):
    return ':'.join([currentTime, entityId, userId])

def deserializeXSRFToken(token):
    (currentTime, entityId, userId) = token.split(':', 2)
    return (currentTime, entityId, userId)

def saltXSRFTokenToBytes(serializedToken):
    tokenBytes = bytearray(serializedToken)
    salt = bytearray(os.urandom(len(tokenBytes)))
    for i in range(len(salt)):
        tokenBytes[i] ^= salt[i]
    return salt + tokenBytes

def unsaltBytestoXSRFToken(saltedBytes):
    if len(saltedBytes) % 2 != 0:
        raise InvalidToken("Salted bytes not divisible by 2")
    originalBytes = saltedBytes[len(saltedBytes)/2:]
    for i in range(len(originalBytes)):
        originalBytes[i] ^= saltedBytes[i]
    return originalBytes.decode()

def encryptXSRFToken(saltedBytes, secretKey):
    # Make copy of input instead of modifying in place
    encrypted = saltedBytes[:]
    secretKeyBytes = bytearray(secretKey)
    for i in range(len(encrypted)):
        encrypted[i] ^= secretKeyBytes[i % len(secretKeyBytes)]
    return encrypted

def decryptXSRFToken(encryptedBytes, secretKey):
    # HA
    return encryptXSRFToken(encryptedBytes, secretKey)

def base64Encode(inputBytes):
    return base64.urlsafe_b64encode(inputBytes).replace('=', '*')

def base64Decode(inputString):
    # Fingers crossed, this seems to work okay!
    return bytearray(base64.urlsafe_b64decode(inputString.replace('*', '=')))
    
# NOTE: This code has a linear time hack that 
#       1. Reveals the secret key
#       2. Completely breaks everything
# PLEASE PLEASE PLEASE Don't use in production.
def GetXSRFToken(secretKey, entityIdStr, userIdStr):
    currentTimeMicros = str(int(time.time() * 1000 * 1000))
    plainXSRF = serializeXSRFToken(currentTimeMicros, entityIdStr, userIdStr)
    saltedBytes = saltXSRFTokenToBytes(plainXSRF)
    encryptedXSRF = encryptXSRFToken(saltedBytes, secretKey)
    return base64Encode(encryptedXSRF)

# This time is one hour
MAX_XSRF_VALIDITITY_MICROS = 3600 * 1000 * 1000

def DecodeXSRFToken(secretKey, tokenString):
    encryptedBytes = base64Decode(tokenString)
    saltedBytes = decryptXSRFToken(encryptedBytes, secretKey)
    plainXSRF = unsaltBytestoXSRFToken(saltedBytes)
    (xsrfTimeMicros, entityIdStr, userIdStr) = deserializeXSRFToken(plainXSRF)
    xsrfTimeDeltaMicros = int(time.time() * 1000 * 1000) - int(xsrfTimeMicros);
    if xsrfTimeDeltaMicros > MAX_XSRF_VALIDITITY_MICROS or xsrfTimeDeltaMicros < 0:
        raise InvalidToken('XSRF Token has expired: Delta Micros: ' + str(xsrfTimeDeltaMicros))
    return (entityIdStr, userIdStr)
