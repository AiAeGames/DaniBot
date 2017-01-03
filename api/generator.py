#API Key generator
import random
import string

def key(length=20):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))