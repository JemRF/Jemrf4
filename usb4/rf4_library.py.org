#----------------
# Verify device ID format
#----------------
def verify_deviceid(deviceid, rf4=1):
    """
    Verifies that the device ID is valid:
    - For rf4=0: must be 2 characters, each 0-9, a-z, or A-Z
    - For rf4=1: must be 4 characters, each 0-9, a-z, or A-Z
    Returns True if valid, False otherwise.
    """
    charset = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if rf4 == 0:
        if len(deviceid) != 2:
            return False
        for c in deviceid:
            if c not in charset:
                return False
    else:
        if len(deviceid) != 4:
            return False
        for c in deviceid:
            if c not in charset:
                return False
    return True
